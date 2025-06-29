from flask import Flask, render_template, request, send_file, abort
import hashlib
import json
import io
import logging

app = Flask(__name__)

# Logging einrichten
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

THR_PRIMARY = "#004372"     # Dunkelblau (Hauptfarbe)
THR_CYAN = "#6FC7EA"        # Cyan (Buttons, Akzente)
THR_BG = "#E5F4FA"          # Hellcyan (leichte Hintergründe)
THR_ACCENT = "#62AD37"      # Grün (Call-to-Actions)
THR_HIGHLIGHT = "#FFB200"   # Orange (Hinweise, Icons, Hover)


MAX_LEAVES = 64
MAX_NAME_LENGTH = 100
MAX_HASHES = 20

def hash_leaf(data):
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def try_parse_json(s, label=""):
    # Akzeptiere nur korrektes JSON (keine Fallbacks)
    logging.info(f"Parsing [{label}]")
    logging.info(s)
    try:
        parsed = json.loads(s)
        logging.info(f"Erfolgreich geladen: {parsed}")
        return parsed
    except Exception as e:
        logging.warning(f"Fehler beim Parsen: {e}")
        return None

def build_merkle_tree(leaves):
    # Sicherheitscheck
    if not leaves or not isinstance(leaves, list):
        raise ValueError("Leavelist fehlt oder ist nicht korrekt formatiert.")
    if len(leaves) > MAX_LEAVES:
        raise ValueError(f"Zu viele Leaves (max. {MAX_LEAVES})")
    tree = []
    layer = [hash_leaf(leaf) for leaf in leaves]
    tree.append(layer)
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        new_layer = []
        for i in range(0, len(layer), 2):
            left = layer[i]
            right = layer[i+1]
            new_layer.append(hashlib.sha256((left + right).encode()).hexdigest())
        tree.append(new_layer)
        layer = new_layer
    return tree

def get_merkle_proof(leaves, index):
    proof = []
    directions = []
    tree = build_merkle_tree(leaves)
    idx = index
    for layer in tree[:-1]:
        sibling_idx = idx ^ 1
        if sibling_idx < len(layer):
            proof.append(layer[sibling_idx])
            directions.append(1 if sibling_idx > idx else 0)
        idx //= 2
    return proof, directions

def verify_merkle_proof(entry, proof, directions, root):
    # Alle Typen checken!
    if not isinstance(entry, str) or not isinstance(root, str):
        raise ValueError("Eintrag und Root müssen Strings sein!")
    if not isinstance(proof, list) or not isinstance(directions, list):
        raise ValueError("Proof und Directions müssen Listen sein!")
    if len(proof) != len(directions):
        raise ValueError("Proof- und Directions-Liste müssen gleich lang sein!")
    if len(proof) > MAX_HASHES:
        raise ValueError(f"Proof zu lang (max {MAX_HASHES})")
    # Namen prüfen
    if not entry or len(entry) > MAX_NAME_LENGTH:
        raise ValueError("Ungültiger Name (leer oder zu lang).")
    # Hashes prüfen
    for h in proof:
        if not isinstance(h, str) or len(h) != 64 or not all(c in "0123456789abcdef" for c in h):
            raise ValueError("Ungültiges Proof-Hash-Format.")
    # Directions prüfen
    for d in directions:
        if d not in (0, 1):
            raise ValueError("Directions darf nur 0 oder 1 enthalten.")
    current = hash_leaf(entry)
    logging.info(f"[Verifikation] Entry: {entry}")
    logging.info(f"  Hash(Leaf): {current}")
    logging.info(f"  Proof: {proof}")
    logging.info(f"  Directions: {directions}")
    for idx, (p, d) in enumerate(zip(proof, directions)):
        if d == 0:
            combined = p + current
        else:
            combined = current + p
        current = hashlib.sha256(combined.encode()).hexdigest()
        logging.info(f"Schritt {idx+1}: Hash: {current}")
    logging.info(f"Erwartete Root: {root}")
    logging.info(f"Berechnete Root: {current}")
    return current == root

@app.route('/')
def index():
    return render_template(
        'index.html',
        th_primary=THR_PRIMARY, th_cyan=THR_CYAN, th_bg=THR_BG, th_accent=THR_ACCENT
    )

@app.route('/create_tree', methods=['GET', 'POST'])
def create_tree():
    error = None
    leaves = []
    if request.method == 'POST':
        leaves = request.form.get('leaves', '').split('\n')
        leaves = [x.strip()[:MAX_NAME_LENGTH] for x in leaves if x.strip()]
        try:
            if not leaves:
                raise ValueError("Bitte mindestens einen Namen angeben!")
            if len(leaves) > MAX_LEAVES:
                raise ValueError(f"Maximal {MAX_LEAVES} Teilnehmer:innen erlaubt.")
            tree = build_merkle_tree(leaves)
            root = tree[-1][0] if tree else ''
            all_proofs = []
            for idx, leaf in enumerate(leaves):
                proof, directions = get_merkle_proof(leaves, idx)
                all_proofs.append({
                    'entry': leaf,
                    'proof': proof,
                    'directions': directions
                })
            tree_json = tree
            export_data = {
                "leaves": leaves,
                "root": root,
                "proofs": all_proofs
            }
            return render_template(
                'create_tree.html',
                leaves=leaves,
                tree=tree,
                root=root,
                all_proofs=all_proofs,
                tree_json=json.dumps(tree_json),
                export_data=json.dumps(export_data, indent=2),
                th_primary=THR_PRIMARY, th_cyan=THR_CYAN, th_bg=THR_BG, th_accent=THR_ACCENT,
                error=None
            )
        except Exception as e:
            error = str(e)
    return render_template(
        'create_tree.html',
        leaves=leaves,
        tree=None,
        root=None,
        all_proofs=None,
        tree_json="[]",
        export_data="{}",
        th_primary=THR_PRIMARY, th_cyan=THR_CYAN, th_bg=THR_BG, th_accent=THR_ACCENT,
        error=error
    )

@app.route('/download_json', methods=['POST'])
def download_json():
    data = request.form.get('json_data', '')
    if not data:
        abort(400, "Keine Daten zum Download übergeben.")
    buf = io.BytesIO()
    buf.write(data.encode('utf-8'))
    buf.seek(0)
    return send_file(buf, mimetype='application/json', as_attachment=True, download_name='merkle_tree.json')

@app.route('/verify_proof', methods=['GET', 'POST'])
def verify_proof():
    result = None
    error = None

    if request.method == 'POST':
        entry = request.form.get('entry', '').strip()
        root = request.form.get('root', '').strip()
        directions_raw = request.form.get('directions', '').strip()
        proof_raw = request.form.get('proof', '').strip()
    else:
        entry = request.args.get('entry', '').strip()
        root = request.args.get('root', '').strip()
        directions_raw = request.args.get('directions', '').strip()
        proof_raw = request.args.get('proof', '').strip()

    directions = try_parse_json(directions_raw, "Directions") if directions_raw else []
    proof = try_parse_json(proof_raw, "Proof") if proof_raw else []

    if request.method == 'POST':
        try:
            if not entry or not root or not proof or not directions:
                raise ValueError("Alle Felder müssen ausgefüllt werden!")
            valid = verify_merkle_proof(entry, proof, directions, root)
            result = "✅ Proof gültig! (Teilnehmer:in ist enthalten)" if valid else "❌ Proof ungültig!"
        except Exception as e:
            error = str(e)

    return render_template(
        'verify_proof.html',
        result=result,
        entry=entry,
        root=root,
        directions=directions_raw,
        proof=proof_raw,
        error=error,
        th_primary=THR_PRIMARY, th_cyan=THR_CYAN, th_bg=THR_BG, th_accent=THR_ACCENT
    )

if __name__ == '__main__':
    app.run(debug=False)  # Niemals debug=True im Produktivbetrieb!
