-- =============================================================================
-- MelodyGen — Schema SQL para Supabase (PostgreSQL)
-- Ejecutar en: Supabase > SQL Editor
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Tabla: users
-- Almacena las credenciales y el estado de créditos de cada usuario.
-- El campo credits_used_today se resetea diariamente via lógica de aplicación
-- comparando last_credit_reset con la fecha actual.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    username            TEXT            UNIQUE NOT NULL,
    password_hash       TEXT            NOT NULL,
    email               TEXT            UNIQUE NOT NULL,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    credits_used_today  INTEGER         NOT NULL DEFAULT 0,
    last_credit_reset   DATE            NOT NULL DEFAULT current_date,
    is_admin            BOOLEAN         NOT NULL DEFAULT false
);

-- ---------------------------------------------------------------------------
-- Tabla: generation_log
-- Registra cada intento de generación musical, incluyendo el costo estimado
-- en USD de la llamada a la API de Replicate y si fue exitosa.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS generation_log (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID            REFERENCES users(id) ON DELETE SET NULL,
    prompt_text         TEXT,
    replicate_cost_usd  NUMERIC(6,4)    NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    success             BOOLEAN         NOT NULL DEFAULT false
);
