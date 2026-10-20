import json
import math
import xml.etree.ElementTree as ET


def distance_metres(lat1, lon1, lat2, lon2):
    R = 6371000  # Rayon de la Terre en mètres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    # Formule de Haversine
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def main():
    # 1. Arrêts TPG (JSON)
    with open("arrets.json", "r", encoding="utf-8") as f:
        arrets = json.load(f)
    print("Nombre d'arrêts chargés :", len(arrets))
    print("Premier arrêt de la liste :", arrets[0]["nomarret"])

    # 2. Collisions TPG (JSON)
    with open("collisions-tpg-avec-tiers.json", "r", encoding="utf-8") as z:
        collisions = json.load(z)
    print("\nNombre collisions TPG :", len(collisions))
    print("Première collision :", collisions[0]["evt_numer"])

    # 3. Accidents généraux SITG (GeoJSON)
    with open("OTC_ACCIDENTS.geojson", "r", encoding="utf-8") as w:
        accidents_sitg = json.load(w)["features"]
    print("\nNombre d'accidents SITG :", len(accidents_sitg))

    # 4. Météo Genève (XML)
    tree = ET.parse("meteo_geneve.xml")
    root = tree.getroot()
    jours_meteo = root.findall("jour")
    print("\nNombre de jours météo chargés :", len(jours_meteo))
    premier_jour = jours_meteo[0]
    print(
        f"Premier jour météo : date={premier_jour.attrib['date']}, "
        f"temp_min={premier_jour.find('temp_min').text}°C, "
        f"pluie={premier_jour.find('pluie_mm').text}mm, "
        f"état={premier_jour.find('etat_chaussee').text}"
    )

    # --- TEST DU CALCUL DE DISTANCE ---
    # Coordonnées Cornavin (46.2098, 6.1426) et Bel-Air (46.2048, 6.1435)
    test_dist = distance_metres(46.2098, 6.1426, 46.2048, 6.1435)
    print(f"\n[Test Haversine] Distance Cornavin -> Bel-Air : {test_dist:.1f} m")



if __name__ == "__main__":
    main()