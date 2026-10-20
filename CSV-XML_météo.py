import xml.etree.ElementTree as ET
import pandas as pd

print("[1/4] Chargement des fichiers CSV MétéoSuisse...")
fichiers = [
    "ogd-smn_gve_h_historical_2010-2019.csv",
    "ogd-smn_gve_h_historical_2020-2029.csv",
]

# Lecture des colonnes utiles uniquement (beaucoup plus rapide)
colonnes_utiles = ["reference_timestamp", "tre200h0", "rre150h0"]
dfs = []
for f in fichiers:
    df_temp = pd.read_csv(
        f, sep=";", usecols=colonnes_utiles, low_memory=False
    )
    dfs.append(df_temp)

df = pd.concat(dfs, ignore_index=True)
print(f"      -> {len(df)} relevés horaires chargés avec succès.")

print("[2/4] Nettoyage et conversion des dates...")
# Conversion du texte en vraies dates (JJ.MM.AAAA HH:mm -> YYYY-MM-DD)
df["date_dt"] = pd.to_datetime(
    df["reference_timestamp"], format="%d.%m.%Y %H:%M", errors="coerce"
)
df["jour"] = df["date_dt"].dt.strftime("%Y-%m-%d")

# Conversion propre des valeurs numériques
df["temperature"] = pd.to_numeric(df["tre200h0"], errors="coerce")
df["pluie"] = pd.to_numeric(df["rre150h0"], errors="coerce").fillna(0.0)

print("[3/4] Agrégation quotidienne (min, max, pluie totale)...")
# Calcul du résumé par jour pour éviter un fichier XML trop lourd
bilan = (
    df.groupby("jour")
    .agg(
        temp_min=("temperature", "min"),
        temp_max=("temperature", "max"),
        pluie_totale=("pluie", "sum"),
    )
    .reset_index()
    .dropna()
)

print("[4/4] Génération du fichier XML structuré (meteo_geneve.xml)...")
root = ET.Element(
    "meteo_geneve_historique",
    station="GVE",
    nom="Genève-Cointrin",
    fournisseur="MeteoSuisse",
)

for _, row in bilan.iterrows():
    t_min = row["temp_min"]
    t_max = row["temp_max"]
    pluie = round(row["pluie_totale"], 1)

    # Estimation de l'état de la route
    if t_min <= 0 and pluie > 0:
        etat = "Verglas/Neige"
    elif pluie > 0:
        etat = "Mouillée"
    else:
        etat = "Sèche"

    jour_elem = ET.SubElement(root, "jour", date=str(row["jour"]))
    ET.SubElement(jour_elem, "temp_min").text = f"{t_min:.1f}"
    ET.SubElement(jour_elem, "temp_max").text = f"{t_max:.1f}"
    ET.SubElement(jour_elem, "pluie_mm").text = f"{pluie:.1f}"
    ET.SubElement(jour_elem, "etat_chaussee").text = etat

# Sauvegarde avec indentation propre
tree = ET.ElementTree(root)
ET.indent(tree, space="  ")
tree.write("meteo_geneve.xml", encoding="utf-8", xml_declaration=True)

print(f"[+] Succès : 'meteo_geneve.xml' a été créé ({len(bilan)} journées) !")