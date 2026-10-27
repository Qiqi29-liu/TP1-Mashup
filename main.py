import json
import math
import unicodedata
import xml.etree.ElementTree as ET

# Normaliser le texte pour que les accents et les tirets sont plus des obstacles pour les recherches
def normaliser(texte):
    if not texte:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texte))
    sans_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
    nettoye = sans_accent.replace("-", " ").replace("'", " ").replace("_", " ")
    return " ".join(nettoye.lower().split())

# Calcule la distance orthodromique ( = diastance à vol d'oiseau sur un surface sphérique) entre deux points GPS (vient de la formule Haversine)
def distance_metres(lat1, lon1, lat2, lon2):
    R = 6371000 # Rayon moyen de la terre 
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Boucle permetant d'entrée un arrêt au minimun dans le sénario 1 , sans revenir sur le menu principal 
def selectionner_arret(arrets):
    while True:
        saisie = input("\nNom de l'arrêt (Entrée pour quitter) : ").strip()
        if not saisie:
            return None

        terme = normaliser(saisie)

        candidats = []
        noms_vus = set()

        for a in arrets:
            coords = a.get("coordonnees")
            nom_brut = a.get("nomarret")
            if nom_brut and coords and isinstance(coords, dict) and coords.get("lat") is not None:
                nom_norm = normaliser(nom_brut)
                if terme in nom_norm:
                    if nom_norm not in noms_vus:
                        candidats.append(a)
                        noms_vus.add(nom_norm)

        if not candidats:
            print(f"Aucun arrêt trouvé pour '{saisie}'.")
            continue
        # Si le nom rentré est correcte la correpondance se fait directe 
        for a in candidats:
            if normaliser(a.get("nomarret")) == terme:
                return a

        if len(candidats) == 1:
            return candidats[0]
        # Si il a peine à s'en souvenir du nom entier ou de l'orthograhe de l'arrêt 
        # On propose lui une liste d'arrêt qui correpond à ce qui l'a entré au paravent 
        print(f"\nArrêts trouvés pour '{saisie}' :")
        limite = min(len(candidats), 8)
        for i in range(limite):
            ar = candidats[i]
            print(f"  {i + 1}. {ar.get('nomarret')} ({ar.get('commune', 'Inconnue')})")

        while True:
            choix = input(f"Choix (1-{limite}, Entrée pour annuler) : ").strip()
            if not choix:
                break
            if choix.isdigit() and 1 <= int(choix) <= limite:
                return candidats[int(choix) - 1]
            print("Choix invalide.")

# Audit de sécurité d'un arrêt TPG en croisant : arrets.json, collisions-tpg-avec-tiers.json et OTC_ACCIDENTS.geojson.
def scenario_1(arrets, collisions, accidents_sitg):
    print("\n--- [Scénario 1 : Audit d'un arrêt TPG] ---")
    arret_cible = selectionner_arret(arrets)
    if not arret_cible:
        return
    # info géographique de l'arrêt
    nom_arret = arret_cible["nomarret"]
    lat_arret = arret_cible["coordonnees"]["lat"]
    lon_arret = arret_cible["coordonnees"]["lon"]

    print(f"\nArrêt sélectionné : {nom_arret} ({arret_cible.get('commune', 'Inconnue')})")
    print(f"Coordonnées       : {lat_arret}, {lon_arret}")
    #collison TPG à cet arrêt
    nom_norm = normaliser(nom_arret)
    collisions_arret = [
        c for c in collisions
        if c.get("arret") and nom_norm in normaliser(c.get("arret"))
    ]
    print(f"Collisions TPG à cet arrêt        : {len(collisions_arret)}")
    #Le totals des accidents cantonaux SITG dans un rayon de 150 mètres
    accidents_proches = []
    for acc in accidents_sitg:
        geom = acc.get("geometry")
        if geom and geom.get("coordinates"):
            lon_acc, lat_acc = geom["coordinates"][0], geom["coordinates"][1]
            if distance_metres(lat_arret, lon_arret, lat_acc, lon_acc) <= 150:
                accidents_proches.append(acc)

    print(f"Accidents cantonaux SITG (< 150m) : {len(accidents_proches)}")

# Impact météo sur les collisions TPG en croisant : les collisions TPG (JSON) avec le fichier météo consolidé (XML) par date
def scenario_2(collisions, jours_meteo):
    print("\n--- [Scénario 2 : Impact météo sur les collisions TPG] ---")
    #décompte du total des différents états de la chaussé 
    meteo_par_date = {}
    total_jours_par_etat = {}

    for jour in jours_meteo:
        d = jour.attrib.get("date")
        etat = jour.find("etat_chaussee")
        if d and etat is not None and etat.text:
            etat_nom = etat.text.strip()
            meteo_par_date[d] = etat_nom
            total_jours_par_etat[etat_nom] = total_jours_par_etat.get(etat_nom, 0) + 1
    # associer chaque collision à la météo du jour
    collisions_par_etat = {}
    for c in collisions:
        d = c.get("jour")
        etat = meteo_par_date.get(d, "Non renseigné")
        collisions_par_etat[etat] = collisions_par_etat.get(etat, 0) + 1

    print("1. Chaussée sèche")
    print("2. Chaussée mouillée")
    print("3. Verglas / Neige")
    print("4. Comparaison complète")
    choix = input("Choix (1-4) : ").strip()

    mapping = {"1": "Sèche", "2": "Mouillée", "3": "Verglas/Neige"}
    #tableau récapitulatif
    if choix in mapping:
        etat_choisi = mapping[choix]
        nb_col = collisions_par_etat.get(etat_choisi, 0)
        nb_j = total_jours_par_etat.get(etat_choisi, 0)
        pct = (nb_col / len(collisions) * 100) if collisions else 0
        moy = (nb_col / nb_j) if nb_j > 0 else 0

        print(f"\nÉtat : {etat_choisi}")
        print(f"Total collisions : {nb_col} ({pct:.1f}%)")
        print(f"Nombre de jours  : {nb_j}")
        print(f"Moyenne par jour : {moy:.2f}")

    elif choix == "4":
        print("-" * 55)
        print(f"{'État chaussée':<18} | {'Collisions':<10} | {'Jours':<6} | {'Moy./j'}")
        print("-" * 55)
        for etat, total_col in collisions_par_etat.items():
            nb_j = total_jours_par_etat.get(etat, 0)
            if nb_j > 0:
                print(f"{etat:<18} | {total_col:<10} | {nb_j:<6} | {total_col / nb_j:.2f}")
            else:
                print(f"{etat:<18} | {total_col:<10} | {'-':<6} | N/A")
        print("-" * 55)
    else:
        print("Choix invalide.")

# Analyse d'une ligne TPG en croisangt : les collisions d'une ligne spécifique avec les coordonnées d'arrets.json
def scenario_3(collisions, arrets):
    print("\n--- [Scénario 3 : Analyse d'une ligne TPG] ---")
    ligne = input("Numéro ou lettre de ligne (ex: 12, 14, F) (Entrée pour quitter) : ").strip().upper()
    if not ligne:
        return
    # Toutes les collisions correspondant à la ligne demandée
    col_ligne = [c for c in collisions if str(c.get("ligne", "")).strip().upper() == ligne]
    if not col_ligne:
        print(f"Aucune donnée pour la ligne {ligne}.")
        return

    coords_arrets = {
        normaliser(a.get("nomarret")): a
        for a in arrets if a.get("nomarret")
    }
    # NB total d'accidents par arrêt sur cette ligne
    compteur = {}
    for c in col_ligne:
        arret = c.get("arret") or "Inconnu"
        compteur[arret] = compteur.get(arret, 0) + 1

    print(f"\nTotal collisions pour la ligne {ligne} : {len(col_ligne)}")
    print("Top 3 des arrêts les plus touchés :")
    print("-" * 65)
    # Les Top 3  avec coordonnées GPS et commune
    top_3 = sorted(compteur.items(), key=lambda x: x[1], reverse=True)[:3]
    for nom, nb in top_3:
        info = coords_arrets.get(normaliser(nom))
        if info and info.get("coordonnees"):
            lat = info["coordonnees"].get("lat")
            lon = info["coordonnees"].get("lon")
            commune = info.get("commune", "Inconnue")
            loc = f"{commune} ({lat}, {lon})"
        else:
            loc = "Localisation non répertoriée"
        print(f" - {nom:<22} : {nb:>3} collisions | {loc}")
    print("-" * 65)

# Bilan territorial par commune en croisant OTC_ACCIDENTS.geojson, arrets.json et collisions-tpg-avec-tiers.json.
def scenario_4(accidents_sitg, arrets, collisions):
    print("\n--- [Scénario 4 : Bilan territorial par commune] ---")
    # Boucle de normalisation
    while True:
        commune = input("\nNom de la commune (Entrée pour quitter) : ").strip()
        if not commune:
            return

        commune_norm = normaliser(commune)

        # Filtrage sans accents/tirets/majuscules grâce à la fonction normaliser
        accidents_com = [
            acc.get("properties", {}) for acc in accidents_sitg
            if commune_norm == normaliser(acc.get("properties", {}).get("COMMUNE", ""))
        ]
        # Total des accidents généraux du SITG sur cette commune
        arrets_com = {
            normaliser(a.get("nomarret"))
            for a in arrets
            if a.get("nomarret") and commune_norm == normaliser(a.get("commune", ""))
        }

        # Si aucun accident ni aucun arrêt n'est trouvé, la commune a été mal saisie alors faudra l'écire corretement. 
        if not accidents_com and not arrets_com:
            print(f"-> Aucune donnée pour '{commune}'. Veuillez écrire correctement le nom de la commune.")
            continue

        # Si trouvée, on fait le total des collisions TPG et on sort de la boucle
        collisions_com = [
            c for c in collisions
            if normaliser(c.get("arret", "")) in arrets_com
        ]
        break
    # Statistiques territoriales et répartition par gravité
    print(f"\nRésultats pour {commune.capitalize()} :")
    print(f" - Arrêts TPG recensés       : {len(arrets_com)}")
    print(f" - Collisions TPG aux arrêts : {len(collisions_com)}")
    print(f" - Accidents généraux (SITG) : {len(accidents_com)}")

    if accidents_com:
        gravite = {}
        for a in accidents_com:
            cons = a.get("CONSEQUENCES", "Non renseigné")
            gravite[cons] = gravite.get(cons, 0) + 1
        print("\nGravité SITG :")
        for k, v in sorted(gravite.items(), key=lambda x: x[1], reverse=True):
            pct = (v / len(accidents_com)) * 100
            print(f" - {k:<25} : {v:>4} ({pct:>4.1f}%)")

#Top 10 des arrêts TPG et accidents aux alentours (SITG) en déterminant le classement des 10 arrêts TPG les plus accidentogènes et calculer le risque routier à 150m.
def scenario_5(collisions, arrets, accidents_sitg):
    print("\n--- [Scénario 5 : Top 10 des arrêts TPG et accidents SITG] ---")

    # Le NB de collisions TPG par arrêt sur l'ensemble du réseau
    compteur = {}
    for c in collisions:
        arret = c.get("arret")
        if arret:
            compteur[arret] = compteur.get(arret, 0) + 1

    top_10 = sorted(compteur.items(), key=lambda x: x[1], reverse=True)[:10]
    # Associer les coordonnées géographiques de chaque arrêt
    geo_arrets = {
        normaliser(a.get("nomarret")): a["coordonnees"]
        for a in arrets
        if a.get("nomarret") and a.get("coordonnees") and isinstance(a.get("coordonnees"), dict) and a["coordonnees"].get("lat")
    }

    # Tableau
    print("-" * 75)
    print(f"{'Rang':<5} | {'Arrêt TPG':<32} | {'Collisions TPG':<16} | {'SITG (<150m)'}")
    print("-" * 75)
    #  calcul les accidents SITG distants de moins de 150m
    for i, (nom, count) in enumerate(top_10, start=1):
        coords = geo_arrets.get(normaliser(nom))
        if coords:
            lat_a, lon_a = coords["lat"], coords["lon"]
            nb_sitg = sum(
                1 for acc in accidents_sitg
                if acc.get("geometry") and acc["geometry"].get("coordinates")
                and distance_metres(lat_a, lon_a, acc["geometry"]["coordinates"][1], acc["geometry"]["coordinates"][0]) <= 150
            )
            sitg_str = str(nb_sitg)
        else:
            sitg_str = "Position N/A"

        print(f"#{i:<4} | {nom:<32} | {count:<16} | {sitg_str}")
    print("-" * 75)

def main():
    print("Chargement des fichiers...")
    
    print(" - Chargement des arrêts TPG (arrets.json)...")
    with open("arrets.json", "r", encoding="utf-8") as f:
        arrets = json.load(f)

    print(" - Chargement des collisions TPG (collisions-tpg-avec-tiers.json)...")
    with open("collisions-tpg-avec-tiers.json", "r", encoding="utf-8") as f:
        collisions = json.load(f)

    print(" - Chargement des accidents généraux (OTC_ACCIDENTS.geojson)...")
    with open("OTC_ACCIDENTS.geojson", "r", encoding="utf-8") as f:
        accidents_sitg = json.load(f)["features"]

    print(" - Chargement de la météo (meteo_geneve.xml)...")
    tree = ET.parse("meteo_geneve.xml")
    jours_meteo = tree.getroot().findall("jour")

    print("Tous les fichiers sont chargés.")

    while True:
        print("\n=== MENU PRINCIPAL ===")
        print("1. Audit d'un arrêt TPG")
        print("2. Impact météo sur les collisions TPG")
        print("3. Analyse d'une ligne TPG")
        print("4. Bilan par commune")
        print("5. Top 10 des arrêts et risque routier environnant")
        print("0. Quitter")

        choix = input("\nVotre choix (0-5) : ").strip()

        if choix == "1":
            scenario_1(arrets, collisions, accidents_sitg)
        elif choix == "2":
            scenario_2(collisions, jours_meteo)
        elif choix == "3":
            scenario_3(collisions, arrets)
        elif choix == "4":
            scenario_4(accidents_sitg, arrets, collisions)
        elif choix == "5":
            scenario_5(collisions, arrets, accidents_sitg)
        elif choix == "0":
            print("Fermeture du programme.")
            break
        else:
            print("Choix invalide.")


if __name__ == "__main__":
    main()