BEGIN;


CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


CREATE TABLE IF NOT EXISTS app_user (
  id            BIGSERIAL PRIMARY KEY,
  name          TEXT NOT NULL,
  username      TEXT,
  email         TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  pro           BOOLEAN DEFAULT FALSE,
);

-- 2) Catégorie / Genre / TypeProduit
CREATE TABLE IF NOT EXISTS categorie (
  id       BIGSERIAL PRIMARY KEY,
  intitule TEXT NOT NULL UNIQUE
);

-- Dans ton diagramme, un Genre est rattaché à une Catégorie (1..n)
CREATE TABLE IF NOT EXISTS genre (
  id          BIGSERIAL PRIMARY KEY,
  intitule    TEXT NOT NULL,
  categorie_id BIGINT NOT NULL REFERENCES categorie(id) ON DELETE CASCADE,
  UNIQUE (categorie_id, intitule)
);

CREATE TABLE IF NOT EXISTS type_produit (
  id           BIGSERIAL PRIMARY KEY,
  nom          TEXT NOT NULL,
  categorie_id BIGINT REFERENCES categorie(id) ON DELETE SET NULL,
  UNIQUE (nom, categorie_id)
);

-- 3) Plateforme + frais
-- (tu as "FraisSupp" + "PourcentageVente" dans ton diagramme)
CREATE TABLE IF NOT EXISTS plateforme (
  id                BIGSERIAL PRIMARY KEY,
  nom               TEXT NOT NULL UNIQUE,
  frais_supp_eur     NUMERIC(12,2) NOT NULL DEFAULT 0,
  pourcentage_vente  NUMERIC(5,2)  NOT NULL DEFAULT 0,
  lien_homepage      TEXT
);

ALTER TABLE plateforme
  ADD CONSTRAINT plateforme_pourcentage_check
  CHECK (pourcentage_vente >= 0 AND pourcentage_vente <= 100);

ALTER TABLE plateforme
  ADD CONSTRAINT plateforme_frais_check
  CHECK (frais_supp_eur >= 0);

-- 4) Stock (inventaire non forcément en vente)
CREATE TABLE IF NOT EXISTS stock (
  id           BIGSERIAL PRIMARY KEY,
  user_id      BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,

  nom          TEXT NOT NULL,
  description  TEXT,
  localisation TEXT,
  A_ete_achete BOOLEAN DEFAULT FALSE,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5) Produit (objet mis en vente / vendu)
CREATE TABLE IF NOT EXISTS produit (
  id               BIGSERIAL PRIMARY KEY,
  user_id          BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,

  nom              TEXT NOT NULL,
  description      TEXT,

  en_vente         BOOLEAN NOT NULL DEFAULT false,
  est_vendu        BOOLEAN NOT NULL DEFAULT false,
  a_ete_achete     BOOLEAN NOT NULL DEFAULT false,

  prix_achat       NUMERIC(12,2) DEFAULT 0,
  prix_vente       NUMERIC(12,2),
  prix_min_espere  NUMERIC(12,2) DEFAULT 0,
  prix_max_espere  NUMERIC(12,2) DEFAULT 0,

  date_mise_en_vente DATE,
  date_vente         DATE,

  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE produit
  ADD CONSTRAINT produit_prix_check
  CHECK (
    (prix_achat IS NULL OR prix_achat >= 0) AND
    (prix_vente IS NULL OR prix_vente >= 0) AND
    (prix_min_espere IS NULL OR prix_min_espere >= 0) AND
    (prix_max_espere IS NULL OR prix_max_espere >= 0)
  );

ALTER TABLE produit
  ADD CONSTRAINT produit_dates_check
  CHECK (
    date_vente IS NULL OR date_mise_en_vente IS NULL OR date_vente >= date_mise_en_vente
  );

-- 6) Produit <-> TypeProduit (many-to-many)
CREATE TABLE IF NOT EXISTS produit_type (
  produit_id BIGINT NOT NULL REFERENCES produit(id) ON DELETE CASCADE,
  type_id    BIGINT NOT NULL REFERENCES type_produit(id) ON DELETE RESTRICT,
  PRIMARY KEY (produit_id, type_id)
);

-- 7) OuVente : Produit posté sur Plateforme + lien annonce
-- (tu veux potentiellement plusieurs plateformes par produit)
CREATE TABLE IF NOT EXISTS ou_vente (
  produit_id   BIGINT NOT NULL REFERENCES produit(id) ON DELETE CASCADE,
  plateforme_id BIGINT NOT NULL REFERENCES plateforme(id) ON DELETE RESTRICT,
  lien         TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (produit_id, plateforme_id)
);

-- 8) Frais annexes (réparation, essence, etc.) rattachés au produit
CREATE TABLE IF NOT EXISTS frais_annexe (
  id         BIGSERIAL PRIMARY KEY,
  produit_id BIGINT NOT NULL REFERENCES produit(id) ON DELETE CASCADE,
  intitule   TEXT NOT NULL,
  montant    NUMERIC(12,2) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE frais_annexe
  ADD CONSTRAINT frais_annexe_montant_check
  CHECK (montant >= 0);

-- 9) Livraison
CREATE TABLE IF NOT EXISTS societe_livraison (
  id   BIGSERIAL PRIMARY KEY,
  nom  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS frais_livraison (
  id          BIGSERIAL PRIMARY KEY,
  produit_id  BIGINT NOT NULL REFERENCES produit(id) ON DELETE CASCADE,
  societe_id  BIGINT REFERENCES societe_livraison(id) ON DELETE SET NULL,
  montant     NUMERIC(12,2) NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE frais_livraison
  ADD CONSTRAINT frais_livraison_montant_check
  CHECK (montant >= 0);

-- 10) Index utiles (perf pour filtres "en vente", "vendu", tri dates)
CREATE INDEX IF NOT EXISTS idx_produit_user ON produit(user_id);
CREATE INDEX IF NOT EXISTS idx_produit_en_vente ON produit(en_vente) WHERE en_vente = true;
CREATE INDEX IF NOT EXISTS idx_produit_est_vendu ON produit(est_vendu) WHERE est_vendu = true;
CREATE INDEX IF NOT EXISTS idx_produit_date_vente ON produit(date_vente);

CREATE INDEX IF NOT EXISTS idx_stock_user ON stock(user_id);

-- 11) Vues pratiques (bénéfice / coût total)
-- coût total = prix_achat + frais annexes + frais livraison + frais plateformes (si vendu ET plateforme connue)
-- Ici on calcule : total_frais_annexes + total_frais_livraison.
-- Les frais plateforme seront calculés plus tard via "vente" ou via une plateforme choisie.
CREATE OR REPLACE VIEW v_produit_couts AS
SELECT
  p.id AS produit_id,
  COALESCE(p.prix_achat, 0) AS prix_achat,
  COALESCE((
    SELECT SUM(fa.montant) FROM frais_annexe fa WHERE fa.produit_id = p.id
  ), 0) AS total_frais_annexes,
  COALESCE((
    SELECT SUM(fl.montant) FROM frais_livraison fl WHERE fl.produit_id = p.id
  ), 0) AS total_frais_livraison,
  (COALESCE(p.prix_achat, 0)
   + COALESCE((SELECT SUM(fa.montant) FROM frais_annexe fa WHERE fa.produit_id = p.id), 0)
   + COALESCE((SELECT SUM(fl.montant) FROM frais_livraison fl WHERE fl.produit_id = p.id), 0)
  ) AS cout_total_hors_plateforme
FROM produit p;

CREATE OR REPLACE VIEW v_produit_benefice_simple AS
SELECT
  p.id AS produit_id,
  p.est_vendu,
  COALESCE(p.prix_vente, 0) AS prix_vente,
  c.cout_total_hors_plateforme,
  (COALESCE(p.prix_vente, 0) - c.cout_total_hors_plateforme) AS benefice_hors_plateforme
FROM produit p
JOIN v_produit_couts c ON c.produit_id = p.id;

-- 12) Marque la migration comme appliquée
INSERT INTO schema_migrations(version) VALUES ('001_init')
ON CONFLICT (version) DO NOTHING;

COMMIT;
