# scripts/import_business_excel.py
# Usage:
#   python scripts/import_business_excel.py --excel /mnt/data/Business.xlsx --user-id 38
# Options:
#   --dry-run   (ne commit pas)
#   --wipe      (supprime d'abord lots/produits de l'user)

import argparse
import os
from datetime import datetime, date
from typing import Any, Optional

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---- Importe tes modèles (adapte les imports si tes paths diffèrent)
from app.models.lot import Lot
from app.models.product import Produit
from app.models.lot_produit import LotProduit


def is_nan(v: Any) -> bool:
    try:
        return pd.isna(v)
    except Exception:
        return v is None


def to_float(v: Any) -> Optional[float]:
    if is_nan(v):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s or s.lower() in {"none", "nan"}:
        return None
    # gère "12,34" si jamais
    s = s.replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def to_int(v: Any) -> Optional[int]:
    if is_nan(v):
        return None
    try:
        return int(v)
    except Exception:
        s = str(v).strip()
        if not s or s.lower() in {"none", "nan"}:
            return None
        try:
            return int(float(s.replace(",", ".")))
        except Exception:
            return None


def to_bool(v: Any) -> Optional[bool]:
    if is_nan(v):
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in {"true", "vrai", "1", "yes", "y"}:
        return True
    if s in {"false", "faux", "0", "no", "n"}:
        return False
    # certains fichiers ont "NONE"
    if s in {"none", "nan", ""}:
        return None
    return None


def to_datetime(v: Any) -> Optional[datetime]:
    if is_nan(v):
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    try:
        ts = pd.to_datetime(v, errors="coerce")
        if pd.isna(ts):
            return None
        return ts.to_pydatetime()
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--excel", required=True, help="Chemin du fichier Business.xlsx")
    parser.add_argument("--user-id", type=int, default=38)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--wipe", action="store_true")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit(
            "DATABASE_URL manquant. Ex: export DATABASE_URL='postgresql+psycopg2://...'"
        )

    engine = create_engine(args.database_url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # --- Lecture Excel
    # Feuille lots
    lots_df = pd.read_excel(args.excel, sheet_name="Feuille 1")
    # Feuille produits
    prod_df = pd.read_excel(args.excel, sheet_name="Feuil1")

    # --- Nettoyage minimal des colonnes attendues
    # Lots: ['Titre', 'Prix_achat', 'date_achat', ..., 'Numero lot']
    lots_df = lots_df.rename(columns={c: str(c).strip() for c in lots_df.columns})
    prod_df = prod_df.rename(columns={c: str(c).strip() for c in prod_df.columns})

    with SessionLocal() as db:
        if args.wipe:
            # Supprime d'abord les liaisons LotProduit via cascade,
            # mais on force un ordre sûr (produits -> lots)
            db.query(Produit).filter(Produit.user_id == args.user_id).delete(synchronize_session=False)
            db.query(Lot).filter(Lot.user_id == args.user_id).delete(synchronize_session=False)
            db.flush()

        # -------------------------
        # 1) Création des lots
        # -------------------------
        lot_by_numero: dict[int, Lot] = {}

        for _, row in lots_df.iterrows():
            numero_lot = to_int(row.get("Numero lot"))
            if not numero_lot:
                continue

            titre = row.get("Titre")
            titre = None if is_nan(titre) else str(titre).strip()
            prix_total = to_float(row.get("Prix_achat")) or 0.0
            date_achat = to_datetime(row.get("date_achat")) or datetime.utcnow()

            lot = Lot(
                user_id=args.user_id,
                titre=titre,
                description=None,
                prix_total_achat=prix_total,
                date_achat=date_achat,
            )
            db.add(lot)
            db.flush()  # pour avoir lot.id
            lot_by_numero[numero_lot] = lot

        # -------------------------
        # 2) Création des produits
        # -------------------------
        created_products = 0
        linked_to_lot = 0

        for _, row in prod_df.iterrows():
            nom = row.get("Pièce")
            if is_nan(nom):
                continue
            nom = str(nom).strip()
            if not nom:
                continue

            prix_min = to_float(row.get("Valeur de Revente Min"))
            prix_max = to_float(row.get("Valeur de revente max"))
            prix_vente = to_float(row.get("Montant Vente"))
            prix_achat_piece = to_float(row.get("Valeur achat nouvelle pièce"))

            en_vente = to_bool(row.get("En Vente"))
            est_vendu = to_bool(row.get("Piece vendu"))

            # si Excel met "NONE" / vide, on retombe sur False par défaut du modèle
            en_vente = bool(en_vente) if en_vente is not None else False
            est_vendu = bool(est_vendu) if est_vendu is not None else False

            # Un produit "acheté" si prix_achat_piece existe OU s'il appartient à un lot
            numero_lot = to_int(row.get("Numero lot"))
            appartient_lot = numero_lot in lot_by_numero if numero_lot else False
            a_ete_achete = bool(prix_achat_piece is not None) or appartient_lot

            produit = Produit(
                nom=nom,
                description=None,
                en_vente=en_vente,
                est_vendu=est_vendu,
                a_ete_achete=a_ete_achete,
                prix_achat=prix_achat_piece,      # prix d’achat individuel si présent
                prix_vente=prix_vente,            # montant de vente si vendu
                prix_min_espere=prix_min or 0.0,
                prix_max_espere=prix_max or 0.0,
                date_mise_en_vente=None,          # pas dans ton Excel
                user_id=args.user_id,
            )
            db.add(produit)
            db.flush()  # pour produit.id
            created_products += 1

            # Liaison au lot si Numero lot présent
            if appartient_lot:
                lot = lot_by_numero[numero_lot]
                link = LotProduit(
                    lot_id=lot.id,
                    produit_id=produit.id,
                    quantite=1,
                    allocation_prix_achat=None,
                    allocation_frais=None,
                    allocation_methode=None,
                )
                db.add(link)
                linked_to_lot += 1

        if args.dry_run:
            db.rollback()
            print(
                f"[DRY-RUN] lots={len(lot_by_numero)} produits={created_products} "
                f"liés_lots={linked_to_lot} user_id={args.user_id}"
            )
        else:
            db.commit()
            print(
                f"[OK] lots={len(lot_by_numero)} produits={created_products} "
                f"liés_lots={linked_to_lot} user_id={args.user_id}"
            )


if __name__ == "__main__":
    main()
