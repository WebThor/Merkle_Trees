# Merkle Tree Live Demo – TH Rosenheim Edition

**Didaktische Web-App zur Live-Visualisierung von Merkle Trees und Proofs**  
_Design im Stil der Technischen Hochschule Rosenheim_

## Features

- Eingabe beliebiger Namen/IDs als Blätter
- Visualisierung des Baums mit Farben, Root-Berechnung
- Alle Proofs als JSON (Directions, Hashes) exportierbar
- Proof-Verifikation mit Schritt-für-Schritt-Anleitung
- Modernes, responsives UI (FH Rosenheim-Farben)
- Fertig für Azure Web App Deployment

## Nutzung

1. **Startseite:**  
   Wähle „Merkle Tree erstellen“ (um den Baum zu bauen und Proofs zu generieren)  
   oder „Merkle Proof verifizieren“ (um einen Nachweis zu prüfen).

2. **Baum erstellen:**  
   - Gib Namen (eine Zeile pro Teilnehmer) ein.
   - Tree + Root werden visualisiert.
   - Proofs & Directions stehen bereit, Export als JSON möglich.

3. **Proof verifizieren:**  
   - Gib Name, Root, Directions (z.B. `[1,0,0]`) und Proof-Hashes (z.B. `["…","…"]`) ein.
   - Ergebnis wird groß angezeigt.

## Azure Deployment

1. Repo auf Azure Web App (Python 3.10+) deployen  
2. Im Azure-Portal unter „Startup Command“ eintragen:  
