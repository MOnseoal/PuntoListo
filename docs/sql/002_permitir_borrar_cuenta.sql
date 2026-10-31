-- =====================================================================
-- PuntoListo · 002 · Permitir borrar una cuenta completa
-- Ejecutar UNA vez en: Supabase > SQL Editor > New query > Run
--
-- Problema: con "on delete restrict", al borrar un usuario desde
-- Supabase > Authentication (o su comercio) la base lo rechazaba si tenía
-- órdenes, porque la regla se revisa en medio del borrado en cascada
-- (antes de que se borren las órdenes).
--
-- Solución: "deferrable initially deferred" hace que la regla se revise al
-- FINAL de la transacción, cuando la cascada ya terminó.
-- - Borrar un cliente o servicio que tiene órdenes sigue PROHIBIDO (23503).
-- - Borrar el comercio completo (o el usuario) ya funciona: se van sus
--   clientes, servicios, órdenes y detalle juntos.
-- =====================================================================

alter table public.ordenes
  drop constraint ordenes_cliente_id_comercio_id_fkey,
  add constraint ordenes_cliente_id_comercio_id_fkey
    foreign key (cliente_id, comercio_id)
    references public.clientes (id, comercio_id) on delete no action
    deferrable initially deferred;

alter table public.orden_servicios
  drop constraint orden_servicios_servicio_id_comercio_id_fkey,
  add constraint orden_servicios_servicio_id_comercio_id_fkey
    foreign key (servicio_id, comercio_id)
    references public.servicios (id, comercio_id) on delete no action
    deferrable initially deferred;
