-- =====================================================================
-- PuntoListo · 004 · Agregar p_descripcion a crear_orden()
-- Ejecutar en: Supabase > SQL Editor > New query > Run
-- Es idempotente: se puede ejecutar varias veces sin error y sin dejar
-- versiones duplicadas (sobrecargas) de la función.
-- =====================================================================

drop function if exists public.crear_orden(bigint, jsonb, date, text);
drop function if exists public.crear_orden(bigint, jsonb, date, text, text);

create or replace function public.crear_orden(
  p_cliente_id     bigint,
  p_servicios      jsonb,
  p_fecha_entrega  date default null,
  p_notas          text default null,
  p_descripcion    text default null
)
returns table (id bigint, folio text)
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_comercio  bigint;
  v_orden     public.ordenes%rowtype;
  v_items     integer;
begin
  select c.id into v_comercio
    from public.comercios c
   where c.usuario_id = auth.uid();

  if v_comercio is null then
    raise exception 'Primero registra tu negocio';
  end if;

  if p_servicios is null
     or jsonb_typeof(p_servicios) <> 'array'
     or jsonb_array_length(p_servicios) = 0 then
    raise exception 'La orden debe incluir al menos un servicio';
  end if;

  insert into public.ordenes (comercio_id, cliente_id, fecha_entrega, notas, descripcion)
  values (
    v_comercio,
    p_cliente_id,
    p_fecha_entrega,
    nullif(trim(p_notas), ''),
    nullif(trim(p_descripcion), '')
  )
  returning * into v_orden;

  insert into public.orden_servicios
    (orden_id, comercio_id, servicio_id, cantidad, precio_unitario)
  select v_orden.id, v_comercio, s.id,
         coalesce((item ->> 'cantidad')::numeric, 1), s.precio
    from jsonb_array_elements(p_servicios) as item
    join public.servicios s
      on s.id = (item ->> 'servicio_id')::bigint
     and s.comercio_id = v_comercio
     and s.activo;

  get diagnostics v_items = row_count;
  if v_items <> jsonb_array_length(p_servicios) then
    raise exception 'Uno o más servicios no existen o están inactivos';
  end if;

  return query select v_orden.id, v_orden.folio;
end;
$$;

revoke execute on function public.crear_orden(bigint, jsonb, date, text, text) from public, anon;
grant  execute on function public.crear_orden(bigint, jsonb, date, text, text) to authenticated;
