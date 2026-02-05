BEGIN;

-- 1) Table vente
CREATE TABLE IF NOT EXISTS vente (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

  produit_id     BIGINT NOT NULL UNIQUE
                 REFERENCES produit(id) ON DELETE CASCADE,

  plateforme_id  BIGINT NOT NULL
                 REFERENCES plateforme(id) ON DELETE RESTRICT,

  prix_vente     NUMERIC(12,2) NOT NULL,

  frais_plateforme_fixe NUMERIC(12,2) NOT NULL DEFAULT 0,
  frais_plateforme_pct  NUMERIC(5,2)  NOT NULL DEFAULT 0,

  montant_frais_plateforme NUMERIC(12,2) NOT NULL,

  date_vente DATE NOT NULL DEFAULT CURRENT_DATE,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2) Contraintes de cohérence
ALTER TABLE vente
  ADD CONSTRAINT vente_prix_check
  CHECK (prix_vente >= 0);

ALTER TABLE vente
  ADD CONSTRAINT vente_frais_fix_check
  CHECK (frais_plateforme_fixe >= 0);

ALTER TABLE vente
  ADD CONSTRAINT vente_frais_pct_check
  CHECK (frais_plateforme_pct >= 0 AND frais_plateforme_pct <= 100);

ALTER TABLE vente
  ADD CONSTRAINT vente_montant_frais_check
  CHECK (montant_frais_plateforme >= 0);

-- 3) Index utiles
CREATE INDEX IF NOT EXISTS idx_vente_produit ON vente(produit_id);
CREATE INDEX IF NOT EXISTS idx_vente_plateforme ON vente(plateforme_id);
CREATE INDEX IF NOT EXISTS idx_vente_date ON vente(date_vente);

-- 4) Vue bénéfice NET par produit (AVEC plateforme)
CREATE OR REPLACE VIEW v_produit_benefice_net AS
SELECT
  p.id AS produit_id,
  p.nom,
  v.date_vente,
  v.prix_vecd backednnte,

  v.montant_frais_plateforme,
  c.cout_total_hors_plateforme,

  (v.prix_vente
   - v.montant_frais_plateforme
   - c.cout_total_hors_plateforme
  ) AS benefice_net
FROM produit p
JOIN vente v ON v.produit_id = p.id
JOIN v_produit_couts c ON c.produit_id = p.id;

-- 5) Marquer la migration comme appliquée
INSERT INTO schema_migrations(version)
VALUES ('002_add_vente')
ON CONFLICT (version) DO NOTHING;

COMMIT;
