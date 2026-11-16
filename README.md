# Service de Mashup Open Data : Sécurité routière et Transports publics à Genève (TP1)

Service en ligne de commande développé en Python permettant d'analyser la sécurité routière et l'accidentologie du réseau des Transports Publics Genevois (TPG) sur la période **2014–2023**, par le croisement de données ouvertes hétérogènes (**JSON**, **GeoJSON** et **XML**).

---

## Sources de données utilisées

* **`arrets.json`** (*JSON*) : Référentiel officiel des arrêts TPG et coordonnées géographiques (TPG Open Data).
* **`collisions-tpg-avec-tiers.json`** (*JSON*) : Historique des collisions impliquant un véhicule TPG (TPG Open Data).
* **`OTC_ACCIDENTS.geojson`** (*GeoJSON*) : Recensement géoréférencé des accidents de la circulation dans le canton de Genève (SITG / Office des transports et de la circulation).
* **`meteo_geneve.xml`** (*XML*) : Relevés météorologiques quotidiens consolidés à la station de Genève-Cointrin, convertis depuis les séries historiques CSV (MétéoSuisse).

---

## Scénarios d'analyse implémentés

1. **Audit de sécurité d'un arrêt TPG :** Croise les collisions TPG à un arrêt donné avec les accidents cantonaux SITG recensés dans un rayon de 150 mètres (calcul via la formule d'Haversine).
2. **Impact météorologique sur les collisions TPG :** Établit la corrélation et la moyenne quotidienne d'incidents selon l'état de la chaussée (`Sèche`, `Mouillée`, `Verglas/Neige`).
3. **Analyse d'une ligne TPG :** Identifie les 3 arrêts les plus touchés sur une ligne spécifique et affiche leur localisation GPS.
4. **Bilan territorial par commune :** Compare la desserte TPG, les collisions aux arrêts et la gravité des accidents routiers généraux à l'échelle d'une commune genevoise.
5. **Palmarès des arrêts à risque (Top 10) :** Classe les 10 arrêts TPG enregistrant le plus d'incidents et mesure la sinistralité routière environnante (< 150 m).

---

## Installation et exécution

### Prérequis
* **Python 3** (aucune bibliothèque externe requise : utilise uniquement les modules standards `json`, `math`, `unicodedata` et `xml.etree.ElementTree`).

### Lancement
Assurez-vous que `main.py` et les 4 fichiers de données se trouvent dans le même répertoire, puis exécutez :

```bash
python3 main.py
