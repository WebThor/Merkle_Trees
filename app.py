from flask import Flask, render_template, request, jsonify, send_file
import hashlib, json, io
import ast

app = Flask(__name__)

# Farben FH Rosenheim Style
THR_PRIMARY = "#004372"
THR_CYAN = "#6fc7ea"
THR_BG = "#f5f7fa"
THR_ACCENT = "#62ad37"

def hash_leaf(data):
    return hashlib.sha256(data.encode()).hexdigest()

def try_parse_json(s, label=""):
    # Log Eingabe
    print(f"\n--- Parsing [{label}] ---")
    print(s)
    try:
        result = json.loads(s)
        print(f"--> Erfolgreich mit json.loads: {result}")
        return result
    except Exception as e:
        print(f"json.loads fehlgeschlagen: {e}")
        try:
            result = ast.literal_eval(s)
            print(f"--> Erfolgreich mit ast.literal_eval: {result}")
            return result
        except Exception as e2:
            print(f"ast.literal_eval fehlgeschlagen: {e2}")
            return []

def build_merkle_tree(leaves):
    tree = []
    layer = [hash_leaf(leaf) for leaf in leaves]
    tree.append(layer)
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])  # Padding: Dupliziere das letzte Element
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
    current = hash_leaf(entry)
    print("\n[Verifikation] Start für Entry:", entry)
    print("  - Hash(Leaf):", current)
    print("  - Proof:", proof)
    print("  - Directions:", directions)
    for idx, (p, d) in enumerate(zip(proof, directions)):
        if d == 0:
            # Sibling links: hash(proof + current)
            combined = p + current
            print(f"  Schritt {idx+1}: d=0  => hash(proof + current)")
            print(f"    proof:   {p}")
            print(f"    current: {current}")
            print(f"    hash_input: {combined}")
            current = hashlib.sha256(combined.encode()).hexdigest()
            print(f"    Ergebnis: {current}")
        else:
            # Sibling rechts: hash(current + proof)
            combined = current + p
            print(f"  Schritt {idx+1}: d=1  => hash(current + proof)")
            print(f"    current: {current}")
            print(f"    proof:   {p}")
            print(f"    hash_input: {combined}")
            current = hashlib.sha256(combined.encode()).hexdigest()
            print(f"    Ergebnis: {current}")
    print("  Erwartete Root:", root)
    print("  Berechnete Root:", current)
    print("  Proof gültig?", current == root)
    return current == root



@app.route('/')
def index():
    return render_template('index.html', th_primary=THR_PRIMARY, th_cyan=THR_CYAN, th_bg=THR_BG, th_accent=THR_ACCENT)

@app.route('/create_tree', methods=['GET', 'POST'])
def create_tree():
    if request.method == 'POST':
        leaves = request.form.get('leaves', '').split('\n')
        leaves = [x.strip() for x in leaves if x.strip()]
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
        # Für die visuelle Darstellung als JSON (z.B. für D3.js)
        tree_json = []
        levelnum = len(tree)
        for level in tree:
            tree_json.append(level)
        # Export als JSON-File
        export_data = {
            "leaves": leaves,
            "root": root,
            "proofs": all_proofs
        }
        return render_template('create_tree.html',
                               leaves=leaves,
                               tree=tree,
                               root=root,
                               all_proofs=all_proofs,
                               tree_json=json.dumps(tree_json),
                               export_data=json.dumps(export_data, indent=2),
                               th_primary=THR_PRIMARY,
                               th_cyan=THR_CYAN,
                               th_bg=THR_BG,
                               th_accent=THR_ACCENT)
    return render_template('create_tree.html', th_primary=THR_PRIMARY, th_cyan=THR_CYAN, th_bg=THR_BG, th_accent=THR_ACCENT)

@app.route('/download_json', methods=['POST'])
def download_json():
    data = request.form.get('json_data', '')
    buf = io.BytesIO()
    buf.write(data.encode('utf-8'))
    buf.seek(0)
    return send_file(buf, mimetype='application/json', as_attachment=True, download_name='merkle_tree.json')

@app.route('/verify_proof', methods=['GET', 'POST'])
def verify_proof():
    result = None
    error = None
    entry = ''
    root = ''
    directions_raw = ''
    proof_raw = ''
    directions = []
    proof = []
    if request.method == 'POST':
        entry = request.form.get('entry', '').strip()
        root = request.form.get('root', '').strip()
        directions_raw = request.form.get('directions', '').strip()
        proof_raw = request.form.get('proof', '').strip()

        print("\n==== Neue Verifikation ====")
        print("Entry:", entry)
        print("Root:", root)
        print("Directions_RAW:", repr(directions_raw))
        print("Proof_RAW:", repr(proof_raw))

        directions = try_parse_json(directions_raw, "Directions")
        proof = try_parse_json(proof_raw, "Proof")
        try:
            if not isinstance(directions, list) or not all(x in [0,1] for x in directions):
                raise ValueError("Directions muss ein Array mit 0 und 1 sein!")
            if not isinstance(proof, list) or not all(isinstance(x, str) and len(x) >= 10 for x in proof):
                raise ValueError("Proof muss ein Array aus Hash-Strings sein!")
            if not entry or not root or not proof or not directions:
                raise ValueError("Alle Felder müssen ausgefüllt werden!")
            print("Starte Verifikation...")
            valid = verify_merkle_proof(entry, proof, directions, root)
            print(f"Proof Verification Ergebnis: {valid}")
            result = "✅ Proof gültig! (Teilnehmer:in ist enthalten)" if valid else "❌ Proof ungültig!"
        except Exception as e:
            print("!!! Fehler bei der Verifikation:", e)
            error = f"{e}"

    return render_template('verify_proof.html',
                           result=result,
                           entry=entry,
                           root=root,
                           directions=directions_raw,
                           proof=proof_raw,
                           error=error,
                           th_primary=THR_PRIMARY,
                           th_cyan=THR_CYAN,
                           th_bg=THR_BG,
                           th_accent=THR_ACCENT)

if __name__ == '__main__':
    app.run(debug=True)
