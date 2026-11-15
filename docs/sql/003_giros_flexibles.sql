-- =====================================================================
-- PuntoListo · 003 · Giros flexibles y descripción de la orden
-- Ejecutar en: Supabase > SQL Editor > New query > Run
-- =====================================================================

-- 1. Quitar el CHECK fijo de giro en comercios y plantillas_servicio
alter table public.comercios
  drop constraint if exists comercios_giro_check;

alter table public.comercios
  add constraint comercios_giro_check
  check (length(trim(giro)) between 2 and 30);

alter table public.plantillas_servicio
  drop constraint if exists plantillas_servicio_giro_check;

-- 2. Campo opcional para especificar a qué se dedica cuando elige "otro" (máx. 40)
alter table public.comercios
  add column if not exists giro_otro text
  check (giro_otro is null or length(trim(giro_otro)) <= 40);

-- 3. Descripción corta de lo que dejó el cliente en la orden (máx. 200)
alter table public.ordenes
  add column if not exists descripcion text
  check (descripcion is null or length(trim(descripcion)) <= 200);
