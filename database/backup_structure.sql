--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Ubuntu 16.9-1.pgdg24.04+1)
-- Dumped by pg_dump version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)

-- Started on 2025-09-02 17:49:43 -03

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE pro_team_care_11;
--
-- TOC entry 4226 (class 1262 OID 85929)
-- Name: pro_team_care_11; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE pro_team_care_11 WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'C.UTF-8';


ALTER DATABASE pro_team_care_11 OWNER TO postgres;

\connect pro_team_care_11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 4227 (class 0 OID 0)
-- Name: pro_team_care_11; Type: DATABASE PROPERTIES; Schema: -; Owner: postgres
--

ALTER DATABASE pro_team_care_11 SET search_path TO 'master', 'public';


\connect pro_team_care_11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 6 (class 2615 OID 85930)
-- Name: master; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA master;


ALTER SCHEMA master OWNER TO postgres;

--
-- TOC entry 301 (class 1255 OID 85931)
-- Name: fn_addresses_quality_score(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_addresses_quality_score() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.quality_score := master.fn_calculate_address_quality_score(
                    NEW.street, NEW.number, NEW.neighborhood,
                    NEW.city, NEW.state, NEW.zip_code,
                    NEW.latitude, NEW.longitude
                );
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_addresses_quality_score() OWNER TO postgres;

--
-- TOC entry 302 (class 1255 OID 85932)
-- Name: fn_audit_trigger_lgpd(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_audit_trigger_lgpd() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
    DECLARE
        operation_type_val varchar(50);
        affected_data jsonb;
        current_user_id bigint;
        current_context_type varchar(20);
        current_context_id bigint;
        data_category_val varchar(50);
        sensitivity_level varchar(20);
        person_id_val bigint;
    BEGIN
        -- Determinar tipo de operação
        IF TG_OP = 'DELETE' THEN
            operation_type_val := 'delete';
            affected_data := to_jsonb(OLD);
        ELSIF TG_OP = 'INSERT' THEN
            operation_type_val := 'create';
            affected_data := to_jsonb(NEW);
        ELSIF TG_OP = 'UPDATE' THEN
            operation_type_val := 'update';
            affected_data := to_jsonb(NEW);
        END IF;

        -- Obter contexto atual da sessão (com fallbacks seguros)
        current_user_id := 1; -- Default sistema
        current_context_type := 'system';
        current_context_id := NULL;

        -- Determinar categoria e sensibilidade baseado na tabela
        data_category_val := TG_ARGV[0]; -- Passado como parâmetro do trigger
        sensitivity_level := TG_ARGV[1]; -- Passado como parâmetro do trigger

        -- Determinar person_id baseado na tabela
        IF TG_TABLE_NAME = 'people' THEN
            person_id_val := COALESCE(NEW.id, OLD.id);
        ELSIF TG_TABLE_NAME = 'users' THEN
            person_id_val := COALESCE(NEW.id, OLD.id);
        ELSIF TG_TABLE_NAME IN ('addresses', 'phones', 'emails') THEN
            -- Para tabelas polimórficas, tentar encontrar person_id
            person_id_val := 1; -- Fallback por enquanto
        ELSIF TG_TABLE_NAME IN ('companies', 'clients', 'professionals') THEN
            -- Buscar person_id via relacionamento
            IF TG_TABLE_NAME = 'companies' THEN
                SELECT person_id INTO person_id_val FROM companies WHERE id = COALESCE(NEW.id, OLD.id);
            ELSIF TG_TABLE_NAME = 'clients' THEN
                SELECT person_id INTO person_id_val FROM clients WHERE id = COALESCE(NEW.id, OLD.id);
            ELSIF TG_TABLE_NAME = 'professionals' THEN
                SELECT person_id INTO person_id_val FROM professionals WHERE id = COALESCE(NEW.id, OLD.id);
            END IF;
            person_id_val := COALESCE(person_id_val, 1);
        ELSE
            person_id_val := 1;
        END IF;

        -- Registrar na tabela de auditoria LGPD
        INSERT INTO data_privacy_logs (
            operation_type,
            data_category,
            person_id,
            operator_id,
            context_type,
            context_id,
            purpose,
            legal_basis,
            data_fields,
            is_sensitive_data,
            consent_id,
            created_at,
            compliance_notes
        ) VALUES (
            operation_type_val,
            data_category_val,
            person_id_val,
            current_user_id,
            current_context_type,
            current_context_id,
            'Operação automática via trigger - ' || TG_OP || ' em ' || TG_TABLE_NAME,
            CASE
                WHEN sensitivity_level = 'high' THEN 'legal_obligation'
                WHEN sensitivity_level = 'medium' THEN 'legitimate_interests'
                ELSE 'contract'
            END,
            affected_data::json,
            CASE WHEN sensitivity_level = 'high' THEN true ELSE false END,
            NULL,
            NOW(),
            'Auditoria automática LGPD - Trigger: ' || TG_NAME || ' | Tabela: ' || TG_TABLE_NAME || ' | Operação: ' || TG_OP
        );

        -- Retornar o registro apropriado
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        ELSE
            RETURN NEW;
        END IF;
    END;
    $$;


ALTER FUNCTION master.fn_audit_trigger_lgpd() OWNER TO postgres;

--
-- TOC entry 4228 (class 0 OID 0)
-- Dependencies: 302
-- Name: FUNCTION fn_audit_trigger_lgpd(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_audit_trigger_lgpd() IS 'Função genérica para auditoria automática LGPD - registra todas as operações DML em data_privacy_logs';


--
-- TOC entry 303 (class 1255 OID 85933)
-- Name: fn_calculate_address_quality_score(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_calculate_address_quality_score() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    score INTEGER := 0;
BEGIN
    -- Campos básicos obrigatórios (40 pontos)
    IF NEW.street IS NOT NULL AND LENGTH(TRIM(NEW.street)) > 0 THEN score := score + 10; END IF;
    IF NEW.neighborhood IS NOT NULL AND LENGTH(TRIM(NEW.neighborhood)) > 0 THEN score := score + 10; END IF;
    IF NEW.city IS NOT NULL AND LENGTH(TRIM(NEW.city)) > 0 THEN score := score + 10; END IF;
    IF NEW.zip_code IS NOT NULL AND LENGTH(NEW.zip_code) = 8 THEN score := score + 10; END IF;

    -- Campos complementares (30 pontos)
    IF NEW.number IS NOT NULL AND LENGTH(TRIM(NEW.number)) > 0 THEN score := score + 15; END IF;
    IF NEW.state IS NOT NULL AND LENGTH(NEW.state) = 2 THEN score := score + 15; END IF;

    -- Dados de APIs (30 pontos)
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN score := score + 15; END IF;
    IF NEW.api_data IS NOT NULL AND jsonb_array_length(NEW.api_data->'sources') > 0 THEN score := score + 15; END IF;

    NEW.quality_score := score;
    RETURN NEW;
END;
$$;


ALTER FUNCTION master.fn_calculate_address_quality_score() OWNER TO postgres;

--
-- TOC entry 4229 (class 0 OID 0)
-- Dependencies: 303
-- Name: FUNCTION fn_calculate_address_quality_score(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_calculate_address_quality_score() IS 'Calcula score de qualidade (0-100) baseado na completude dos dados do endereço.';


--
-- TOC entry 304 (class 1255 OID 85934)
-- Name: fn_calculate_address_quality_score(text, text, text, text, text, text, numeric, numeric); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_calculate_address_quality_score(street text, number text, neighborhood text, city text, state text, zip_code text, latitude numeric DEFAULT NULL::numeric, longitude numeric DEFAULT NULL::numeric) RETURNS integer
    LANGUAGE plpgsql IMMUTABLE
    AS $_$
        DECLARE
            score integer := 0;
        BEGIN
            -- Pontuação baseada na completude dos dados
            IF street IS NOT NULL AND length(trim(street)) > 0 THEN score := score + 20; END IF;
            IF number IS NOT NULL AND length(trim(number)) > 0 THEN score := score + 15; END IF;
            IF neighborhood IS NOT NULL AND length(trim(neighborhood)) > 0 THEN score := score + 15; END IF;
            IF city IS NOT NULL AND length(trim(city)) > 0 THEN score := score + 15; END IF;
            IF state IS NOT NULL AND length(trim(state)) = 2 THEN score := score + 10; END IF;
            IF zip_code IS NOT NULL AND zip_code ~ '^[0-9]{5}-?[0-9]{3}$' THEN score := score + 10; END IF;
            IF latitude IS NOT NULL AND longitude IS NOT NULL THEN score := score + 15; END IF;

            RETURN LEAST(score, 100);
        END;
        $_$;


ALTER FUNCTION master.fn_calculate_address_quality_score(street text, number text, neighborhood text, city text, state text, zip_code text, latitude numeric, longitude numeric) OWNER TO postgres;

--
-- TOC entry 305 (class 1255 OID 85935)
-- Name: fn_calculate_consent_checksum(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_calculate_consent_checksum() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    consent_data TEXT;
BEGIN
    consent_data := CONCAT(
        NEW.person_id, '|',
        NEW.consent_type, '|',
        NEW.purpose, '|',
        NEW.consent_text, '|',
        NEW.version, '|',
        NEW.given_at
    );
    NEW.checksum := encode(digest(consent_data, 'sha256'), 'hex');
    RETURN NEW;
END;
$$;


ALTER FUNCTION master.fn_calculate_consent_checksum() OWNER TO postgres;

--
-- TOC entry 306 (class 1255 OID 85936)
-- Name: fn_calculate_context_duration(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_calculate_context_duration() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Se está finalizando o contexto, calcular duração
    IF OLD.ended_at IS NULL AND NEW.ended_at IS NOT NULL THEN
        NEW.duration_seconds := EXTRACT(EPOCH FROM (NEW.ended_at - NEW.switched_at))::INTEGER;
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION master.fn_calculate_context_duration() OWNER TO postgres;

--
-- TOC entry 4230 (class 0 OID 0)
-- Dependencies: 306
-- Name: FUNCTION fn_calculate_context_duration(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_calculate_context_duration() IS 'Calcula a duração em segundos quando um contexto de usuário é finalizado.';


--
-- TOC entry 307 (class 1255 OID 85937)
-- Name: fn_calculate_distance_between_addresses(bigint, bigint); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_calculate_distance_between_addresses(address_id_1 bigint, address_id_2 bigint) RETURNS numeric
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    lat1 NUMERIC;
    lon1 NUMERIC;
    lat2 NUMERIC;
    lon2 NUMERIC;
    distance_meters NUMERIC;
BEGIN
    -- Buscar coordenadas do primeiro endereço
    SELECT latitude, longitude INTO lat1, lon1
    FROM master.addresses
    WHERE id = address_id_1
    AND latitude IS NOT NULL
    AND longitude IS NOT NULL;

    -- Buscar coordenadas do segundo endereço
    SELECT latitude, longitude INTO lat2, lon2
    FROM master.addresses
    WHERE id = address_id_2
    AND latitude IS NOT NULL
    AND longitude IS NOT NULL;

    -- Verificar se ambos endereços têm coordenadas
    IF lat1 IS NULL OR lon1 IS NULL OR lat2 IS NULL OR lon2 IS NULL THEN
        RETURN NULL;
    END IF;

    -- Calcular distância usando earthdistance
    SELECT earth_distance(
        ll_to_earth(lat1, lon1),
        ll_to_earth(lat2, lon2)
    ) INTO distance_meters;

    RETURN ROUND(distance_meters / 1000, 2); -- Retorna em quilômetros
END;
$$;


ALTER FUNCTION master.fn_calculate_distance_between_addresses(address_id_1 bigint, address_id_2 bigint) OWNER TO postgres;

--
-- TOC entry 4231 (class 0 OID 0)
-- Dependencies: 307
-- Name: FUNCTION fn_calculate_distance_between_addresses(address_id_1 bigint, address_id_2 bigint); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_calculate_distance_between_addresses(address_id_1 bigint, address_id_2 bigint) IS 'Calcula a distância em quilômetros entre dois endereços usando suas coordenadas.';


--
-- TOC entry 308 (class 1255 OID 85938)
-- Name: fn_can_manage_role(bigint, bigint); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_can_manage_role(manager_role_id bigint, target_role_id bigint) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    manager_level INTEGER;
    target_level INTEGER;
    manager_context VARCHAR(20);
    target_context VARCHAR(20);
BEGIN
    -- Buscar dados dos papéis
    SELECT level, context_type INTO manager_level, manager_context
    FROM master.roles WHERE id = manager_role_id;

    SELECT level, context_type INTO target_level, target_context
    FROM master.roles WHERE id = target_role_id;

    -- Super admin pode gerenciar tudo
    IF manager_context = 'system' AND manager_level >= 100 THEN
        RETURN true;
    END IF;

    -- Admin da empresa pode gerenciar roles de establishment
    IF manager_context = 'company' AND target_context = 'establishment' THEN
        RETURN true;
    END IF;

    -- Dentro do mesmo contexto, nível maior pode gerenciar menor
    IF manager_context = target_context AND manager_level > target_level THEN
        RETURN true;
    END IF;

    RETURN false;
END;
$$;


ALTER FUNCTION master.fn_can_manage_role(manager_role_id bigint, target_role_id bigint) OWNER TO postgres;

--
-- TOC entry 309 (class 1255 OID 85939)
-- Name: fn_check_person_type(bigint, character varying); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_check_person_type(p_person_id bigint, p_expected_type character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
        DECLARE
            actual_type varchar(2);
        BEGIN
            SELECT person_type INTO actual_type
            FROM master.people
            WHERE id = p_person_id;

            RETURN actual_type = p_expected_type;
        END;
        $$;


ALTER FUNCTION master.fn_check_person_type(p_person_id bigint, p_expected_type character varying) OWNER TO postgres;

--
-- TOC entry 4232 (class 0 OID 0)
-- Dependencies: 309
-- Name: FUNCTION fn_check_person_type(p_person_id bigint, p_expected_type character varying); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_check_person_type(p_person_id bigint, p_expected_type character varying) IS 'Verifica se um registro em master.people tem o person_type esperado. Usado em CHECK constraints.';


--
-- TOC entry 310 (class 1255 OID 85940)
-- Name: fn_check_single_principal_address(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_check_single_principal_address() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                IF NEW.is_principal = true THEN
                    UPDATE master.addresses
                    SET is_principal = false
                    WHERE addressable_type = NEW.addressable_type
                    AND addressable_id = NEW.addressable_id
                    AND id != NEW.id;
                END IF;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_check_single_principal_address() OWNER TO postgres;

--
-- TOC entry 4233 (class 0 OID 0)
-- Dependencies: 310
-- Name: FUNCTION fn_check_single_principal_address(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_check_single_principal_address() IS 'Garante a unicidade do campo is_principal = true por entidade polimórfica.';


--
-- TOC entry 311 (class 1255 OID 85941)
-- Name: fn_check_single_principal_email(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_check_single_principal_email() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                IF NEW.is_principal = true THEN
                    UPDATE master.emails
                    SET is_principal = false
                    WHERE emailable_type = NEW.emailable_type
                    AND emailable_id = NEW.emailable_id
                    AND id != NEW.id;
                END IF;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_check_single_principal_email() OWNER TO postgres;

--
-- TOC entry 4234 (class 0 OID 0)
-- Dependencies: 311
-- Name: FUNCTION fn_check_single_principal_email(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_check_single_principal_email() IS 'Garante a unicidade do campo is_principal = true por entidade polimórfica.';


--
-- TOC entry 312 (class 1255 OID 85942)
-- Name: fn_check_single_principal_establishment(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_check_single_principal_establishment() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                IF NEW.is_principal = true THEN
                    UPDATE master.establishments
                    SET is_principal = false
                    WHERE company_id = NEW.company_id
                    AND id != NEW.id;
                END IF;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_check_single_principal_establishment() OWNER TO postgres;

--
-- TOC entry 4235 (class 0 OID 0)
-- Dependencies: 312
-- Name: FUNCTION fn_check_single_principal_establishment(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_check_single_principal_establishment() IS 'Garante a unicidade do campo is_principal = true por company_id.';


--
-- TOC entry 313 (class 1255 OID 85943)
-- Name: fn_check_single_principal_phone(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_check_single_principal_phone() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                IF NEW.is_principal = true THEN
                    UPDATE master.phones
                    SET is_principal = false
                    WHERE phoneable_type = NEW.phoneable_type
                    AND phoneable_id = NEW.phoneable_id
                    AND id != NEW.id;
                END IF;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_check_single_principal_phone() OWNER TO postgres;

--
-- TOC entry 4236 (class 0 OID 0)
-- Dependencies: 313
-- Name: FUNCTION fn_check_single_principal_phone(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_check_single_principal_phone() IS 'Garante a unicidade do campo is_principal = true por entidade polimórfica.';


--
-- TOC entry 314 (class 1255 OID 85944)
-- Name: fn_cleanup_expired_lgpd_data(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_cleanup_expired_lgpd_data() RETURNS integer
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
            DECLARE
                deleted_count INTEGER := 0;
                retention_days INTEGER := 2555; -- 7 anos padrão LGPD
            BEGIN
                -- Limpar data_privacy_logs expirados
                DELETE FROM data_privacy_logs
                WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;

                GET DIAGNOSTICS deleted_count = ROW_COUNT;

                -- Log da operação de limpeza
                INSERT INTO data_privacy_logs (
                    operation_type, data_category, person_id, operator_id,
                    context_type, purpose, legal_basis, data_fields,
                    is_sensitive_data, created_at, compliance_notes
                ) VALUES (
                    'maintenance', 'sistema', 1, 1, 'system',
                    'Limpeza automática de logs expirados LGPD',
                    'legal_obligation',
                    jsonb_build_object('deleted_records', deleted_count, 'retention_days', retention_days),
                    false, NOW(),
                    'Limpeza automática executada - ' || deleted_count || ' registros removidos'
                );

                RETURN deleted_count;
            END;
            $$;


ALTER FUNCTION master.fn_cleanup_expired_lgpd_data() OWNER TO postgres;

--
-- TOC entry 4237 (class 0 OID 0)
-- Dependencies: 314
-- Name: FUNCTION fn_cleanup_expired_lgpd_data(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_cleanup_expired_lgpd_data() IS 'Função para limpeza automática de dados LGPD expirados conforme política de retenção';


--
-- TOC entry 315 (class 1255 OID 85945)
-- Name: fn_cleanup_old_activity_log_partitions(integer); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_cleanup_old_activity_log_partitions(months_to_keep integer DEFAULT 12) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    partition_record RECORD;
    cutoff_date DATE;
    dropped_count INTEGER := 0;
BEGIN
    cutoff_date := date_trunc('month', NOW() - (months_to_keep || ' months')::INTERVAL);

    FOR partition_record IN
        SELECT child.relname AS partition_name
        FROM pg_inherits
        JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
        JOIN pg_class child ON pg_inherits.inhrelid = child.oid
        WHERE parent.relname = 'activity_logs'
        AND child.relname < 'activity_logs_' || to_char(cutoff_date, 'YYYY_MM')
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS master.' || quote_ident(partition_record.partition_name);
        dropped_count := dropped_count + 1;
    END LOOP;

    RETURN dropped_count;
END;
$$;


ALTER FUNCTION master.fn_cleanup_old_activity_log_partitions(months_to_keep integer) OWNER TO postgres;

--
-- TOC entry 4238 (class 0 OID 0)
-- Dependencies: 315
-- Name: FUNCTION fn_cleanup_old_activity_log_partitions(months_to_keep integer); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_cleanup_old_activity_log_partitions(months_to_keep integer) IS 'Remove partições da tabela activity_logs mais antigas que o número de meses especificado.';


--
-- TOC entry 316 (class 1255 OID 85946)
-- Name: fn_copy_role_permissions(bigint, bigint, bigint); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_copy_role_permissions(p_source_role_id bigint, p_target_role_id bigint, p_granted_by_user_id bigint DEFAULT NULL::bigint) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    copied_count INTEGER;
BEGIN
    -- Copiar permissões
    INSERT INTO master.role_permissions (role_id, permission_id, granted_by_user_id)
    SELECT
        p_target_role_id,
        rp.permission_id,
        p_granted_by_user_id
    FROM master.role_permissions rp
    WHERE rp.role_id = p_source_role_id
    ON CONFLICT (role_id, permission_id) DO NOTHING;

    GET DIAGNOSTICS copied_count = ROW_COUNT;

    RETURN copied_count;
END;
$$;


ALTER FUNCTION master.fn_copy_role_permissions(p_source_role_id bigint, p_target_role_id bigint, p_granted_by_user_id bigint) OWNER TO postgres;

--
-- TOC entry 317 (class 1255 OID 85947)
-- Name: fn_coverage_area_stats(numeric, numeric, numeric); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_coverage_area_stats(center_lat numeric, center_lon numeric, max_radius_km numeric DEFAULT 50) RETURNS TABLE(total_addresses bigint, within_5km bigint, within_10km bigint, within_25km bigint, avg_distance_km numeric, max_distance_km numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_addresses,
        COUNT(*) FILTER (WHERE earth_distance(ll_to_earth(center_lat, center_lon), ll_to_earth(a.latitude, a.longitude)) <= 5000) as within_5km,
        COUNT(*) FILTER (WHERE earth_distance(ll_to_earth(center_lat, center_lon), ll_to_earth(a.latitude, a.longitude)) <= 10000) as within_10km,
        COUNT(*) FILTER (WHERE earth_distance(ll_to_earth(center_lat, center_lon), ll_to_earth(a.latitude, a.longitude)) <= 25000) as within_25km,
        AVG(earth_distance(ll_to_earth(center_lat, center_lon), ll_to_earth(a.latitude, a.longitude)) / 1000)::NUMERIC(10,2) as avg_distance_km,
        MAX(earth_distance(ll_to_earth(center_lat, center_lon), ll_to_earth(a.latitude, a.longitude)) / 1000)::NUMERIC(10,2) as max_distance_km
    FROM master.addresses a
    WHERE a.latitude IS NOT NULL
    AND a.longitude IS NOT NULL
    AND a.is_active = true
    AND earth_distance(ll_to_earth(center_lat, center_lon), ll_to_earth(a.latitude, a.longitude)) <= (max_radius_km * 1000);
END;
$$;


ALTER FUNCTION master.fn_coverage_area_stats(center_lat numeric, center_lon numeric, max_radius_km numeric) OWNER TO postgres;

--
-- TOC entry 318 (class 1255 OID 85948)
-- Name: fn_create_activity_log_partition(date); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_create_activity_log_partition(p_date date) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    partition_name TEXT;
    start_of_month TEXT;
    end_of_month TEXT;
BEGIN
    partition_name := 'activity_logs_' || to_char(p_date, 'YYYY_MM');
    start_of_month := to_char(p_date, 'YYYY-MM-01');
    end_of_month := to_char(p_date + INTERVAL '1 month', 'YYYY-MM-01');

    IF NOT EXISTS(SELECT FROM pg_class WHERE relname = partition_name AND relkind = 'r') THEN
        EXECUTE format(
            'CREATE TABLE master.%I PARTITION OF master.activity_logs FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            start_of_month,
            end_of_month
        );
    END IF;
END;
$$;


ALTER FUNCTION master.fn_create_activity_log_partition(p_date date) OWNER TO postgres;

--
-- TOC entry 4239 (class 0 OID 0)
-- Dependencies: 318
-- Name: FUNCTION fn_create_activity_log_partition(p_date date); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_create_activity_log_partition(p_date date) IS 'Cria uma nova partição mensal para a tabela activity_logs se ela ainda não existir.';


--
-- TOC entry 319 (class 1255 OID 85949)
-- Name: fn_create_crud_permissions(character varying, character varying, character varying, boolean); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_create_crud_permissions(p_module character varying, p_resource character varying, p_context_level character varying DEFAULT 'establishment'::character varying, p_include_manage boolean DEFAULT false) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    created_count INTEGER := 0;
BEGIN
    -- View
    PERFORM fn_create_permission(p_module, 'view', p_resource, p_context_level);
    created_count := created_count + 1;

    -- Create
    PERFORM fn_create_permission(p_module, 'create', p_resource, p_context_level);
    created_count := created_count + 1;

    -- Update
    PERFORM fn_create_permission(p_module, 'update', p_resource, p_context_level);
    created_count := created_count + 1;

    -- Delete
    PERFORM fn_create_permission(p_module, 'delete', p_resource, p_context_level);
    created_count := created_count + 1;

    -- Manage (opcional)
    IF p_include_manage THEN
        PERFORM fn_create_permission(p_module, 'manage', p_resource, p_context_level);
        created_count := created_count + 1;
    END IF;

    RETURN created_count;
EXCEPTION
    WHEN unique_violation THEN
        -- Permissões já existem, retornar 0
        RETURN 0;
END;
$$;


ALTER FUNCTION master.fn_create_crud_permissions(p_module character varying, p_resource character varying, p_context_level character varying, p_include_manage boolean) OWNER TO postgres;

--
-- TOC entry 320 (class 1255 OID 85950)
-- Name: fn_create_permission(character varying, character varying, character varying, character varying, character varying, text); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_create_permission(p_module character varying, p_action character varying, p_resource character varying, p_context_level character varying DEFAULT 'establishment'::character varying, p_display_name character varying DEFAULT NULL::character varying, p_description text DEFAULT NULL::text) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
    permission_name VARCHAR(125);
    permission_display VARCHAR(200);
    new_permission_id BIGINT;
BEGIN
    -- Gerar nome padronizado
    permission_name := LOWER(p_action || '-' || p_resource);
    IF p_module != 'general' THEN
        permission_name := LOWER(p_module || '-' || permission_name);
    END IF;

    -- Gerar display name se não fornecido
    IF p_display_name IS NULL THEN
        permission_display := INITCAP(p_action) || ' ' || REPLACE(INITCAP(p_resource), '_', ' ');
        IF p_module != 'general' THEN
            permission_display := INITCAP(p_module) || ': ' || permission_display;
        END IF;
    ELSE
        permission_display := p_display_name;
    END IF;

    -- Inserir permissão
    INSERT INTO master.permissions (
        name,
        display_name,
        description,
        module,
        action,
        resource,
        context_level
    ) VALUES (
        permission_name,
        permission_display,
        COALESCE(p_description, 'Permissão para ' || LOWER(p_action) || ' em ' || REPLACE(LOWER(p_resource), '_', ' ')),
        LOWER(p_module),
        LOWER(p_action),
        LOWER(p_resource),
        p_context_level
    ) RETURNING id INTO new_permission_id;

    RETURN new_permission_id;
END;
$$;


ALTER FUNCTION master.fn_create_permission(p_module character varying, p_action character varying, p_resource character varying, p_context_level character varying, p_display_name character varying, p_description text) OWNER TO postgres;

--
-- TOC entry 321 (class 1255 OID 85951)
-- Name: fn_create_role(character varying, character varying, text, integer, character varying); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_create_role(p_name character varying, p_display_name character varying, p_description text DEFAULT NULL::text, p_level integer DEFAULT 50, p_context_type character varying DEFAULT 'establishment'::character varying) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
    new_role_id BIGINT;
BEGIN
    -- Validações
    IF p_name IS NULL OR LENGTH(TRIM(p_name)) = 0 THEN
        RAISE EXCEPTION 'Nome do papel é obrigatório';
    END IF;

    IF p_display_name IS NULL OR LENGTH(TRIM(p_display_name)) = 0 THEN
        RAISE EXCEPTION 'Nome de exibição é obrigatório';
    END IF;

    -- Inserir novo papel
    INSERT INTO master.roles (
        name,
        display_name,
        description,
        level,
        context_type,
        is_system_role
    ) VALUES (
        LOWER(TRIM(p_name)),
        TRIM(p_display_name),
        TRIM(p_description),
        p_level,
        p_context_type,
        false
    ) RETURNING id INTO new_role_id;

    RETURN new_role_id;
END;
$$;


ALTER FUNCTION master.fn_create_role(p_name character varying, p_display_name character varying, p_description text, p_level integer, p_context_type character varying) OWNER TO postgres;

--
-- TOC entry 322 (class 1255 OID 85952)
-- Name: fn_find_addresses_within_radius(numeric, numeric, numeric); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_find_addresses_within_radius(center_latitude numeric, center_longitude numeric, radius_km numeric DEFAULT 10) RETURNS TABLE(id bigint, full_address text, distance_km numeric, addressable_type character varying, addressable_id bigint)
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        CONCAT_WS(', ', a.street, a.number, a.neighborhood, a.city, a.state) as full_address,
        ROUND(
            earth_distance(
                ll_to_earth(center_latitude, center_longitude),
                ll_to_earth(a.latitude, a.longitude)
            ) / 1000, 2
        ) as distance_km,
        a.addressable_type::VARCHAR(50),
        a.addressable_id
    FROM master.addresses a
    WHERE a.latitude IS NOT NULL
    AND a.longitude IS NOT NULL
    AND earth_distance(
        ll_to_earth(center_latitude, center_longitude),
        ll_to_earth(a.latitude, a.longitude)
    ) <= (radius_km * 1000)
    ORDER BY earth_distance(
        ll_to_earth(center_latitude, center_longitude),
        ll_to_earth(a.latitude, a.longitude)
    );
END;
$$;


ALTER FUNCTION master.fn_find_addresses_within_radius(center_latitude numeric, center_longitude numeric, radius_km numeric) OWNER TO postgres;

--
-- TOC entry 4240 (class 0 OID 0)
-- Dependencies: 322
-- Name: FUNCTION fn_find_addresses_within_radius(center_latitude numeric, center_longitude numeric, radius_km numeric); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_find_addresses_within_radius(center_latitude numeric, center_longitude numeric, radius_km numeric) IS 'Busca endereços dentro de um raio específico (em km) a partir de coordenadas centrais.';


--
-- TOC entry 323 (class 1255 OID 85953)
-- Name: fn_find_closest_address(numeric, numeric, text); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_find_closest_address(reference_lat numeric, reference_lon numeric, target_addressable_type text DEFAULT NULL::text) RETURNS TABLE(id bigint, full_address text, distance_km numeric, addressable_type text, addressable_id bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        CONCAT_WS(', ', a.street, a.number, a.neighborhood, a.city, a.state) as full_address,
        (earth_distance(
            ll_to_earth(reference_lat, reference_lon),
            ll_to_earth(a.latitude, a.longitude)
        ) / 1000)::NUMERIC(10,2) as distance_km,
        a.addressable_type::TEXT,
        a.addressable_id
    FROM master.addresses a
    WHERE a.latitude IS NOT NULL
    AND a.longitude IS NOT NULL
    AND a.is_active = true
    AND (target_addressable_type IS NULL OR a.addressable_type = target_addressable_type)
    ORDER BY earth_distance(
        ll_to_earth(reference_lat, reference_lon),
        ll_to_earth(a.latitude, a.longitude)
    )
    LIMIT 1;
END;
$$;


ALTER FUNCTION master.fn_find_closest_address(reference_lat numeric, reference_lon numeric, target_addressable_type text) OWNER TO postgres;

--
-- TOC entry 324 (class 1255 OID 85954)
-- Name: fn_find_nearby_addresses(numeric, numeric, numeric); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_find_nearby_addresses(center_lat numeric, center_lon numeric, radius_km numeric DEFAULT 10) RETURNS TABLE(id bigint, full_address text, distance_km numeric, addressable_type text, addressable_id bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        CONCAT_WS(', ', a.street, a.number, a.neighborhood, a.city, a.state) as full_address,
        (earth_distance(
            ll_to_earth(center_lat, center_lon),
            ll_to_earth(a.latitude, a.longitude)
        ) / 1000)::NUMERIC(10,2) as distance_km,
        a.addressable_type::TEXT,
        a.addressable_id
    FROM master.addresses a
    WHERE a.latitude IS NOT NULL
    AND a.longitude IS NOT NULL
    AND earth_distance(
        ll_to_earth(center_lat, center_lon),
        ll_to_earth(a.latitude, a.longitude)
    ) <= (radius_km * 1000)
    ORDER BY earth_distance(
        ll_to_earth(center_lat, center_lon),
        ll_to_earth(a.latitude, a.longitude)
    );
END;
$$;


ALTER FUNCTION master.fn_find_nearby_addresses(center_lat numeric, center_lon numeric, radius_km numeric) OWNER TO postgres;

--
-- TOC entry 325 (class 1255 OID 85955)
-- Name: fn_format_whatsapp_number(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_format_whatsapp_number() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Só processar se for WhatsApp e for celular
    IF NEW.is_whatsapp = true AND NEW.type = 'mobile' AND LENGTH(NEW.number) = 11 THEN
        -- Formato para WhatsApp: +55DDDnúmero (sem espaços)
        NEW.whatsapp_formatted := '+' || NEW.country_code || NEW.number;
    ELSE
        NEW.whatsapp_formatted := NULL;
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION master.fn_format_whatsapp_number() OWNER TO postgres;

--
-- TOC entry 4241 (class 0 OID 0)
-- Dependencies: 325
-- Name: FUNCTION fn_format_whatsapp_number(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_format_whatsapp_number() IS 'Formata número para links do WhatsApp quando aplicável.';


--
-- TOC entry 326 (class 1255 OID 85956)
-- Name: fn_format_whatsapp_number(text, text); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_format_whatsapp_number(country_code text DEFAULT '55'::text, phone_number text DEFAULT NULL::text) RETURNS text
    LANGUAGE plpgsql IMMUTABLE
    AS $$
        DECLARE
            clean_number text;
        BEGIN
            IF phone_number IS NULL OR phone_number = '' THEN
                RETURN NULL;
            END IF;

            -- Remove caracteres especiais
            clean_number := regexp_replace(phone_number, '[^0-9]', '', 'g');

            -- Formato: +5511999999999
            RETURN '+' || country_code || clean_number;
        END;
        $$;


ALTER FUNCTION master.fn_format_whatsapp_number(country_code text, phone_number text) OWNER TO postgres;

--
-- TOC entry 327 (class 1255 OID 85957)
-- Name: fn_get_establishment_setting(bigint, character varying); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_get_establishment_setting(p_establishment_id bigint, p_setting_key character varying) RETURNS jsonb
    LANGUAGE plpgsql STABLE
    AS $$
DECLARE
    setting_value JSONB;
    company_id_val BIGINT;
    company_setting_value JSONB;
BEGIN
    -- 1. Tenta obter a configuração específica do estabelecimento
    SELECT es.setting_value INTO setting_value
    FROM master.establishment_settings es
    WHERE es.establishment_id = p_establishment_id
    AND es.setting_key = p_setting_key;

    -- Se encontrou um valor (mesmo que seja 'null' jsonb), retorna ele
    IF FOUND THEN
        RETURN setting_value;
    END IF;

    -- 2. Se não encontrou, busca a configuração da empresa mãe para herança
    SELECT e.company_id INTO company_id_val
    FROM master.establishments e
    WHERE e.id = p_establishment_id;

    IF company_id_val IS NOT NULL THEN
        SELECT cs.setting_value INTO company_setting_value
        FROM master.company_settings cs
        WHERE cs.company_id = company_id_val
        AND cs.setting_key = p_setting_key;

        IF FOUND THEN
            RETURN company_setting_value;
        END IF;
    END IF;

    -- 3. Se não encontrou em nenhum nível, retorna NULL
    RETURN NULL;
END;
$$;


ALTER FUNCTION master.fn_get_establishment_setting(p_establishment_id bigint, p_setting_key character varying) OWNER TO postgres;

--
-- TOC entry 4242 (class 0 OID 0)
-- Dependencies: 327
-- Name: FUNCTION fn_get_establishment_setting(p_establishment_id bigint, p_setting_key character varying); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_get_establishment_setting(p_establishment_id bigint, p_setting_key character varying) IS 'Obtém o valor de uma configuração para um estabelecimento, aplicando a lógica de herança da empresa se um valor específico não for encontrado.';


--
-- TOC entry 328 (class 1255 OID 85958)
-- Name: fn_get_permissions_by_context(character varying, character varying); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_get_permissions_by_context(p_context_level character varying DEFAULT NULL::character varying, p_module character varying DEFAULT NULL::character varying) RETURNS TABLE(id bigint, name character varying, display_name character varying, module character varying, action character varying, resource character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.name,
        p.display_name,
        p.module,
        p.action,
        p.resource
    FROM master.permissions p
    WHERE p.is_active = true
    AND (p_context_level IS NULL OR p.context_level = p_context_level)
    AND (p_module IS NULL OR p.module = p_module)
    ORDER BY p.module, p.action, p.resource;
END;
$$;


ALTER FUNCTION master.fn_get_permissions_by_context(p_context_level character varying, p_module character varying) OWNER TO postgres;

--
-- TOC entry 329 (class 1255 OID 85959)
-- Name: fn_get_roles_by_context(character varying, integer, integer); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_get_roles_by_context(p_context_type character varying DEFAULT NULL::character varying, p_min_level integer DEFAULT 0, p_max_level integer DEFAULT 100) RETURNS TABLE(id bigint, name character varying, display_name character varying, level integer, context_type character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.id,
        r.name,
        r.display_name,
        r.level,
        r.context_type
    FROM master.roles r
    WHERE r.is_active = true
    AND (p_context_type IS NULL OR r.context_type = p_context_type)
    AND r.level BETWEEN p_min_level AND p_max_level
    ORDER BY r.level DESC, r.name;
END;
$$;


ALTER FUNCTION master.fn_get_roles_by_context(p_context_type character varying, p_min_level integer, p_max_level integer) OWNER TO postgres;

--
-- TOC entry 330 (class 1255 OID 85960)
-- Name: fn_grant_multiple_permissions(bigint, bigint[], bigint); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_grant_multiple_permissions(p_role_id bigint, p_permission_ids bigint[], p_granted_by_user_id bigint DEFAULT NULL::bigint) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    permission_id BIGINT;
    granted_count INTEGER := 0;
BEGIN
    -- Iterar sobre array de permission_ids
    FOREACH permission_id IN ARRAY p_permission_ids
    LOOP
        BEGIN
            PERFORM fn_grant_permission_to_role(p_role_id, permission_id, p_granted_by_user_id);
            granted_count := granted_count + 1;
        EXCEPTION
            WHEN OTHERS THEN
                -- Log do erro mas continua processamento
                RAISE NOTICE 'Erro ao conceder permissão % para papel %: %', permission_id, p_role_id, SQLERRM;
        END;
    END LOOP;

    RETURN granted_count;
END;
$$;


ALTER FUNCTION master.fn_grant_multiple_permissions(p_role_id bigint, p_permission_ids bigint[], p_granted_by_user_id bigint) OWNER TO postgres;

--
-- TOC entry 331 (class 1255 OID 85961)
-- Name: fn_grant_permission_to_role(bigint, bigint, bigint); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_grant_permission_to_role(p_role_id bigint, p_permission_id bigint, p_granted_by_user_id bigint DEFAULT NULL::bigint) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    role_exists BOOLEAN;
    permission_exists BOOLEAN;
BEGIN
    -- Verificar se papel existe e está ativo
    SELECT EXISTS(
        SELECT 1 FROM master.roles
        WHERE id = p_role_id AND is_active = true
    ) INTO role_exists;

    IF NOT role_exists THEN
        RAISE EXCEPTION 'Papel com ID % não existe ou está inativo', p_role_id;
    END IF;

    -- Verificar se permissão existe e está ativa
    SELECT EXISTS(
        SELECT 1 FROM master.permissions
        WHERE id = p_permission_id AND is_active = true
    ) INTO permission_exists;

    IF NOT permission_exists THEN
        RAISE EXCEPTION 'Permissão com ID % não existe ou está inativa', p_permission_id;
    END IF;

    -- Inserir relacionamento (ON CONFLICT para evitar duplicatas)
    INSERT INTO master.role_permissions (role_id, permission_id, granted_by_user_id)
    VALUES (p_role_id, p_permission_id, p_granted_by_user_id)
    ON CONFLICT (role_id, permission_id) DO NOTHING;

    RETURN true;
END;
$$;


ALTER FUNCTION master.fn_grant_permission_to_role(p_role_id bigint, p_permission_id bigint, p_granted_by_user_id bigint) OWNER TO postgres;

--
-- TOC entry 332 (class 1255 OID 85962)
-- Name: fn_lgpd_automatic_audit(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_lgpd_automatic_audit() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
        DECLARE
            audit_config RECORD;
            current_user_id BIGINT;
            current_ip VARCHAR(45);
            current_session VARCHAR(255);
            sensitivity_level VARCHAR(50);
            lawful_basis VARCHAR(100);
            operation_type VARCHAR(20);
        BEGIN
            -- Determine operation type
            IF TG_OP = 'DELETE' THEN
                operation_type := 'DELETE';
            ELSIF TG_OP = 'UPDATE' THEN
                operation_type := 'UPDATE';
            ELSIF TG_OP = 'INSERT' THEN
                operation_type := 'INSERT';
            END IF;

            -- Get audit configuration for this table/operation
            SELECT * INTO audit_config
            FROM master.lgpd_audit_config
            WHERE table_name = TG_TABLE_NAME
            AND operation = operation_type
            AND audit_enabled = true;

            -- Skip if auditing is disabled for this table/operation
            IF NOT FOUND THEN
                RETURN COALESCE(NEW, OLD);
            END IF;

            -- Get current context (this would be set by application)
            current_user_id := COALESCE(current_setting('app.current_user_id', true)::BIGINT, 0);
            current_ip := COALESCE(current_setting('app.current_ip', true), '127.0.0.1');
            current_session := current_setting('app.current_session_id', true);
            sensitivity_level := COALESCE(audit_config.data_sensitivity_level, 'internal');

            -- Determine lawful basis based on context
            lawful_basis := COALESCE(current_setting('app.lawful_basis', true), 'legitimate_interests');

            -- Insert audit record
            INSERT INTO master.activity_logs (
                log_name,
                description,
                subject_type,
                subject_id,
                event,
                causer_type,
                causer_id,
                properties,
                created_at,
                ip_address,
                session_id,
                business_justification,
                data_sensitivity_level,
                processing_lawful_basis
            ) VALUES (
                'lgpd_auto_audit',
                'Automatic LGPD audit for ' || TG_TABLE_NAME || ' ' || operation_type,
                'App\Models\\' || initcap(TG_TABLE_NAME),
                COALESCE(NEW.id, OLD.id)::TEXT,
                lower(operation_type),
                'App\Models\User',
                NULLIF(current_user_id, 0),
                jsonb_build_object(
                    'table', TG_TABLE_NAME,
                    'operation', operation_type,
                    'old_values', CASE WHEN TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE NULL END,
                    'new_values', CASE WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN to_jsonb(NEW) ELSE NULL END,
                    'sensitive_columns', audit_config.sensitive_columns,
                    'automatic_audit', true
                ),
                NOW(),
                current_ip,
                current_session,
                COALESCE(current_setting('app.business_justification', true), 'System operation - ' || operation_type),
                sensitivity_level,
                lawful_basis
            );

            -- For sensitive data operations, also log in data_privacy_logs
            IF sensitivity_level IN ('sensitive_personal', 'highly_sensitive') THEN
                INSERT INTO master.data_privacy_logs (
                    operation_type,
                    data_category,
                    person_id,
                    operator_id,
                    purpose,
                    legal_basis,
                    data_fields,
                    is_sensitive_data,
                    created_at,
                    compliance_notes
                ) VALUES (
                    operation_type,
                    TG_TABLE_NAME,
                    CASE
                        WHEN TG_TABLE_NAME = 'people' THEN COALESCE(NEW.id, OLD.id)
                        WHEN TG_TABLE_NAME IN ('addresses', 'phones', 'emails') THEN (
                            SELECT p.id FROM master.people p
                            WHERE p.id = CASE
                                WHEN TG_TABLE_NAME = 'addresses' THEN COALESCE(NEW.addressable_id, OLD.addressable_id)
                                WHEN TG_TABLE_NAME = 'phones' THEN COALESCE(NEW.phoneable_id, OLD.phoneable_id)
                                WHEN TG_TABLE_NAME = 'emails' THEN COALESCE(NEW.emailable_id, OLD.emailable_id)
                            END
                        )
                        ELSE NULL
                    END,
                    NULLIF(current_user_id, 0),
                    COALESCE(current_setting('app.processing_purpose', true), 'System maintenance'),
                    lawful_basis,
                    jsonb_build_object(
                        'affected_columns', audit_config.sensitive_columns,
                        'operation_details', jsonb_build_object(
                            'table', TG_TABLE_NAME,
                            'record_id', COALESCE(NEW.id, OLD.id),
                            'timestamp', NOW()
                        )
                    ),
                    true,
                    NOW(),
                    'Automatic LGPD audit trigger - ' || operation_type || ' on ' || TG_TABLE_NAME
                );
            END IF;

            RETURN COALESCE(NEW, OLD);
        EXCEPTION
            WHEN OTHERS THEN
                -- Log the error but don't fail the original operation
                RAISE WARNING 'LGPD audit trigger failed: %', SQLERRM;
                RETURN COALESCE(NEW, OLD);
        END;
        $$;


ALTER FUNCTION master.fn_lgpd_automatic_audit() OWNER TO postgres;

--
-- TOC entry 333 (class 1255 OID 85963)
-- Name: fn_lgpd_query_audit(character varying, jsonb, integer, text, character varying); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_lgpd_query_audit(p_table_name character varying, p_records_accessed jsonb DEFAULT NULL::jsonb, p_records_count integer DEFAULT 0, p_query_purpose text DEFAULT 'System query'::text, p_lawful_basis character varying DEFAULT 'legitimate_interests'::character varying) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
        DECLARE
            current_user_id BIGINT;
            current_ip VARCHAR(45);
            current_session VARCHAR(255);
            sensitivity_level VARCHAR(50);
        BEGIN
            -- Get current context
            current_user_id := COALESCE(current_setting('app.current_user_id', true)::BIGINT, 0);
            current_ip := COALESCE(current_setting('app.current_ip', true), '127.0.0.1');
            current_session := current_setting('app.current_session_id', true);

            -- Get sensitivity level for table
            SELECT data_sensitivity_level INTO sensitivity_level
            FROM master.lgpd_audit_config
            WHERE table_name = p_table_name
            AND operation = 'SELECT'
            AND audit_enabled = true;

            -- Skip if no config found or auditing disabled
            IF NOT FOUND THEN
                RETURN;
            END IF;

            -- Insert query audit record
            INSERT INTO master.query_audit_logs (
                user_id,
                ip_address,
                session_id,
                table_accessed,
                records_accessed,
                records_count,
                query_purpose,
                lawful_basis,
                data_sensitivity_level,
                access_context,
                application_module
            ) VALUES (
                NULLIF(current_user_id, 0),
                current_ip,
                current_session,
                p_table_name,
                p_records_accessed,
                p_records_count,
                p_query_purpose,
                p_lawful_basis,
                sensitivity_level,
                COALESCE(current_setting('app.access_context', true), 'System access'),
                COALESCE(current_setting('app.module_name', true), 'Unknown')
            );

        EXCEPTION
            WHEN OTHERS THEN
                -- Log error but don't interrupt the query
                RAISE WARNING 'Query audit failed: %', SQLERRM;
        END;
        $$;


ALTER FUNCTION master.fn_lgpd_query_audit(p_table_name character varying, p_records_accessed jsonb, p_records_count integer, p_query_purpose text, p_lawful_basis character varying) OWNER TO postgres;

--
-- TOC entry 334 (class 1255 OID 85964)
-- Name: fn_log_data_privacy_operation(bigint, character varying, character varying, character varying, character varying, bigint, jsonb, boolean, bigint); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_log_data_privacy_operation(p_person_id bigint, p_operation_type character varying, p_data_category character varying, p_purpose character varying, p_legal_basis character varying, p_operator_id bigint DEFAULT NULL::bigint, p_data_fields jsonb DEFAULT NULL::jsonb, p_is_sensitive_data boolean DEFAULT false, p_consent_id bigint DEFAULT NULL::bigint) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
    new_log_id BIGINT;
BEGIN
    INSERT INTO master.data_privacy_logs (
        person_id,
        operation_type,
        data_category,
        purpose,
        legal_basis,
        operator_id,
        data_fields,
        is_sensitive_data,
        consent_id
    ) VALUES (
        p_person_id,
        p_operation_type,
        p_data_category,
        p_purpose,
        p_legal_basis,
        p_operator_id,
        p_data_fields,
        p_is_sensitive_data,
        p_consent_id
    ) RETURNING id INTO new_log_id;

    RETURN new_log_id;
END;
$$;


ALTER FUNCTION master.fn_log_data_privacy_operation(p_person_id bigint, p_operation_type character varying, p_data_category character varying, p_purpose character varying, p_legal_basis character varying, p_operator_id bigint, p_data_fields jsonb, p_is_sensitive_data boolean, p_consent_id bigint) OWNER TO postgres;

--
-- TOC entry 4243 (class 0 OID 0)
-- Dependencies: 334
-- Name: FUNCTION fn_log_data_privacy_operation(p_person_id bigint, p_operation_type character varying, p_data_category character varying, p_purpose character varying, p_legal_basis character varying, p_operator_id bigint, p_data_fields jsonb, p_is_sensitive_data boolean, p_consent_id bigint); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_log_data_privacy_operation(p_person_id bigint, p_operation_type character varying, p_data_category character varying, p_purpose character varying, p_legal_basis character varying, p_operator_id bigint, p_data_fields jsonb, p_is_sensitive_data boolean, p_consent_id bigint) IS 'Registra uma operação de privacidade de dados para fins de auditoria LGPD.';


--
-- TOC entry 335 (class 1255 OID 85965)
-- Name: fn_permission_exists(character varying, character varying, character varying, character varying); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_permission_exists(p_module character varying, p_action character varying, p_resource character varying, p_context_level character varying DEFAULT 'establishment'::character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    permission_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO permission_count
    FROM master.permissions
    WHERE module = LOWER(p_module)
    AND action = LOWER(p_action)
    AND resource = LOWER(p_resource)
    AND context_level = p_context_level
    AND is_active = true;

    RETURN permission_count > 0;
END;
$$;


ALTER FUNCTION master.fn_permission_exists(p_module character varying, p_action character varying, p_resource character varying, p_context_level character varying) OWNER TO postgres;

--
-- TOC entry 336 (class 1255 OID 85966)
-- Name: fn_phones_format_whatsapp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_phones_format_whatsapp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                IF NEW.is_whatsapp = true AND NEW.number IS NOT NULL THEN
                    NEW.whatsapp_formatted := master.fn_format_whatsapp_number(NEW.country_code, NEW.number);
                END IF;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_phones_format_whatsapp() OWNER TO postgres;

--
-- TOC entry 337 (class 1255 OID 85967)
-- Name: fn_protect_system_roles(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_protect_system_roles() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                IF OLD.is_system_role = true AND (
                    OLD.name != NEW.name OR
                    OLD.level != NEW.level OR
                    NEW.is_system_role = false
                ) THEN
                    RAISE EXCEPTION 'Cannot modify system roles';
                END IF;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_protect_system_roles() OWNER TO postgres;

--
-- TOC entry 338 (class 1255 OID 85968)
-- Name: fn_revoke_permission_from_role(bigint, bigint); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_revoke_permission_from_role(p_role_id bigint, p_permission_id bigint) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM master.role_permissions
    WHERE role_id = p_role_id AND permission_id = p_permission_id;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count > 0;
END;
$$;


ALTER FUNCTION master.fn_revoke_permission_from_role(p_role_id bigint, p_permission_id bigint) OWNER TO postgres;

--
-- TOC entry 339 (class 1255 OID 85969)
-- Name: fn_schedule_cleanup_trigger(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_schedule_cleanup_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                -- Esta função seria chamada por um job agendado
                -- Por enquanto apenas registra que deveria executar limpeza
                INSERT INTO data_privacy_logs (
                    operation_type, data_category, person_id, operator_id,
                    context_type, purpose, legal_basis, data_fields,
                    is_sensitive_data, created_at, compliance_notes
                ) VALUES (
                    'maintenance', 'agendamento', 1, 1, 'system',
                    'Agendamento de limpeza LGPD identificado',
                    'legal_obligation',
                    jsonb_build_object('trigger_time', NOW()),
                    false, NOW(),
                    'Sistema identificou necessidade de executar limpeza automática LGPD'
                );

                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_schedule_cleanup_trigger() OWNER TO postgres;

--
-- TOC entry 340 (class 1255 OID 85970)
-- Name: fn_set_document_retention_date(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_set_document_retention_date() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Se contém dados pessoais e não foi definida data de retenção
    IF NEW.contains_personal_data = true AND NEW.data_retention_expires_at IS NULL THEN
        -- Definir para 5 anos após criação (padrão LGPD)
        NEW.data_retention_expires_at = NEW.created_at + INTERVAL '5 years';
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION master.fn_set_document_retention_date() OWNER TO postgres;

--
-- TOC entry 4244 (class 0 OID 0)
-- Dependencies: 340
-- Name: FUNCTION fn_set_document_retention_date(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_set_document_retention_date() IS 'Define data de retenção LGPD para documentos que contêm dados pessoais.';


--
-- TOC entry 341 (class 1255 OID 85971)
-- Name: fn_set_establishment_setting(bigint, character varying, jsonb, bigint); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_set_establishment_setting(p_establishment_id bigint, p_setting_key character varying, p_setting_value jsonb, p_updated_by_user_id bigint DEFAULT NULL::bigint) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO master.establishment_settings (
        establishment_id,
        setting_key,
        setting_category, -- Categoria e nome podem vir de uma tabela de metadados no futuro
        setting_name,
        setting_value,
        updated_by_user_id
    ) VALUES (
        p_establishment_id,
        p_setting_key,
        split_part(p_setting_key, '.', 1),
        p_setting_key,
        p_setting_value,
        p_updated_by_user_id
    )
    ON CONFLICT (establishment_id, setting_key)
    DO UPDATE SET
        setting_value = EXCLUDED.setting_value,
        updated_at = NOW(),
        updated_by_user_id = EXCLUDED.updated_by_user_id;

    RETURN true;
END;
$$;


ALTER FUNCTION master.fn_set_establishment_setting(p_establishment_id bigint, p_setting_key character varying, p_setting_value jsonb, p_updated_by_user_id bigint) OWNER TO postgres;

--
-- TOC entry 4245 (class 0 OID 0)
-- Dependencies: 341
-- Name: FUNCTION fn_set_establishment_setting(p_establishment_id bigint, p_setting_key character varying, p_setting_value jsonb, p_updated_by_user_id bigint); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_set_establishment_setting(p_establishment_id bigint, p_setting_key character varying, p_setting_value jsonb, p_updated_by_user_id bigint) IS 'Define ou atualiza o valor de uma configuração para um estabelecimento específico.';


--
-- TOC entry 342 (class 1255 OID 85972)
-- Name: fn_setup_default_role_permissions(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_setup_default_role_permissions() RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    result_log TEXT := '';
    role_record RECORD;
    permission_ids BIGINT[];
BEGIN
    -- SUPER ADMIN: Todas as permissões
    SELECT array_agg(id) INTO permission_ids FROM master.permissions WHERE is_active = true;
    PERFORM fn_grant_multiple_permissions(
        (SELECT id FROM master.roles WHERE name = 'super_admin'),
        permission_ids
    );
    result_log := result_log || 'Super Admin: ' || array_length(permission_ids, 1) || ' permissões' || E'\n';

    -- COMPANY ADMIN: Permissões de empresa e estabelecimento
    SELECT array_agg(id) INTO permission_ids
    FROM master.permissions
    WHERE context_level IN ('company', 'establishment')
    AND is_active = true;
    PERFORM fn_grant_multiple_permissions(
        (SELECT id FROM master.roles WHERE name = 'company_admin'),
        permission_ids
    );
    result_log := result_log || 'Company Admin: ' || array_length(permission_ids, 1) || ' permissões' || E'\n';

    -- ESTABLISHMENT ADMIN: Permissões de estabelecimento
    SELECT array_agg(id) INTO permission_ids
    FROM master.permissions
    WHERE context_level = 'establishment'
    AND is_active = true;
    PERFORM fn_grant_multiple_permissions(
        (SELECT id FROM master.roles WHERE name = 'establishment_admin'),
        permission_ids
    );
    result_log := result_log || 'Establishment Admin: ' || array_length(permission_ids, 1) || ' permissões' || E'\n';

    -- MANAGER: Permissões gerenciais básicas
    SELECT array_agg(p.id) INTO permission_ids
    FROM master.permissions p
    WHERE p.context_level = 'establishment'
    AND p.is_active = true
    AND p.action IN ('view', 'create', 'update')
    AND p.module NOT IN ('system', 'users'); -- Excluir gestão de sistema e usuários
    PERFORM fn_grant_multiple_permissions(
        (SELECT id FROM master.roles WHERE name = 'manager'),
        permission_ids
    );
    result_log := result_log || 'Manager: ' || array_length(permission_ids, 1) || ' permissões' || E'\n';

    -- SUPERVISOR: Permissões operacionais
    SELECT array_agg(p.id) INTO permission_ids
    FROM master.permissions p
    WHERE p.context_level = 'establishment'
    AND p.is_active = true
    AND p.action IN ('view', 'create', 'update')
    AND p.module IN ('patients', 'care', 'scheduling', 'documents');
    PERFORM fn_grant_multiple_permissions(
        (SELECT id FROM master.roles WHERE name = 'supervisor'),
        permission_ids
    );
    result_log := result_log || 'Supervisor: ' || array_length(permission_ids, 1) || ' permissões' || E'\n';

    -- OPERATOR: Permissões básicas operacionais
    SELECT array_agg(p.id) INTO permission_ids
    FROM master.permissions p
    WHERE p.context_level = 'establishment'
    AND p.is_active = true
    AND p.action IN ('view', 'create', 'update')
    AND p.module IN ('patients', 'care', 'scheduling')
    AND p.resource NOT LIKE '%sensitive%';
    PERFORM fn_grant_multiple_permissions(
        (SELECT id FROM master.roles WHERE name = 'operator'),
        permission_ids
    );
    result_log := result_log || 'Operator: ' || array_length(permission_ids, 1) || ' permissões' || E'\n';

    -- VIEWER: Apenas visualização
    SELECT array_agg(p.id) INTO permission_ids
    FROM master.permissions p
    WHERE p.context_level = 'establishment'
    AND p.is_active = true
    AND p.action = 'view'
    AND p.resource NOT LIKE '%sensitive%'
    AND p.module NOT IN ('system', 'financial');
    PERFORM fn_grant_multiple_permissions(
        (SELECT id FROM master.roles WHERE name = 'viewer'),
        permission_ids
    );
    result_log := result_log || 'Viewer: ' || array_length(permission_ids, 1) || ' permissões' || E'\n';

    -- ROLES ESPECÍFICOS HOME CARE

    -- NURSE: Permissões de enfermagem
    SELECT array_agg(p.id) INTO permission_ids
    FROM master.permissions p
    WHERE p.context_level = 'establishment'
    AND p.is_active = true
    AND (
        (p.module IN ('patients', 'care', 'scheduling', 'documents') AND p.action IN ('view', 'create', 'update')) OR
        (p.module = 'reports' AND p.action = 'view' AND p.resource = 'basic_reports')
    );
    PERFORM fn_grant_multiple_permissions(
        (SELECT id FROM master.roles WHERE name = 'nurse'),
        permission_ids
    );
    result_log := result_log || 'Nurse: ' || array_length(permission_ids, 1) || ' permissões' || E'\n';

    -- DOCTOR: Permissões médicas
    SELECT array_agg(p.id) INTO permission_ids
    FROM master.permissions p
    WHERE p.context_level = 'establishment'
    AND p.is_active = true
    AND (
        p.module IN ('patients', 'care', 'scheduling', 'documents', 'reports') OR
        (p.module = 'patients' AND p.resource = 'medical_records')
    );
    PERFORM fn_grant_multiple_permissions(
        (SELECT id FROM master.roles WHERE name = 'doctor'),
        permission_ids
    );
    result_log := result_log || 'Doctor: ' || array_length(permission_ids, 1) || ' permissões' || E'\n';

    -- CAREGIVER: Permissões de cuidador
    SELECT array_agg(p.id) INTO permission_ids
    FROM master.permissions p
    WHERE p.context_level = 'establishment'
    AND p.is_active = true
    AND p.module IN ('patients', 'care', 'scheduling')
    AND p.action IN ('view', 'create')
    AND p.resource NOT LIKE '%sensitive%';
    PERFORM fn_grant_multiple_permissions(
        (SELECT id FROM master.roles WHERE name = 'caregiver'),
        permission_ids
    );
    result_log := result_log || 'Caregiver: ' || array_length(permission_ids, 1) || ' permissões' || E'\n';

    RETURN result_log;
END;
$$;


ALTER FUNCTION master.fn_setup_default_role_permissions() OWNER TO postgres;

--
-- TOC entry 343 (class 1255 OID 85973)
-- Name: fn_update_addresses_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_addresses_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_addresses_timestamp() OWNER TO postgres;

--
-- TOC entry 4246 (class 0 OID 0)
-- Dependencies: 343
-- Name: FUNCTION fn_update_addresses_timestamp(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_addresses_timestamp() IS 'Atualiza o timestamp da coluna updated_at em qualquer update na tabela addresses.';


--
-- TOC entry 344 (class 1255 OID 85974)
-- Name: fn_update_clients_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_clients_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_clients_timestamp() OWNER TO postgres;

--
-- TOC entry 4247 (class 0 OID 0)
-- Dependencies: 344
-- Name: FUNCTION fn_update_clients_timestamp(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_clients_timestamp() IS 'Atualiza o timestamp da coluna updated_at em qualquer update na tabela clients.';


--
-- TOC entry 345 (class 1255 OID 85975)
-- Name: fn_update_companies_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_companies_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_companies_timestamp() OWNER TO postgres;

--
-- TOC entry 4248 (class 0 OID 0)
-- Dependencies: 345
-- Name: FUNCTION fn_update_companies_timestamp(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_companies_timestamp() IS 'Atualiza o timestamp da coluna updated_at em qualquer update na tabela companies.';


--
-- TOC entry 346 (class 1255 OID 85976)
-- Name: fn_update_company_settings_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_company_settings_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_company_settings_timestamp() OWNER TO postgres;

--
-- TOC entry 4249 (class 0 OID 0)
-- Dependencies: 346
-- Name: FUNCTION fn_update_company_settings_timestamp(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_company_settings_timestamp() IS 'Atualiza o timestamp da coluna updated_at em qualquer update na tabela company_settings.';


--
-- TOC entry 347 (class 1255 OID 85977)
-- Name: fn_update_consent_records_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_consent_records_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_consent_records_timestamp() OWNER TO postgres;

--
-- TOC entry 348 (class 1255 OID 85978)
-- Name: fn_update_documents_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_documents_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_documents_timestamp() OWNER TO postgres;

--
-- TOC entry 4250 (class 0 OID 0)
-- Dependencies: 348
-- Name: FUNCTION fn_update_documents_timestamp(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_documents_timestamp() IS 'Atualiza o timestamp da coluna updated_at em qualquer update na tabela documents.';


--
-- TOC entry 349 (class 1255 OID 85979)
-- Name: fn_update_emails_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_emails_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_emails_timestamp() OWNER TO postgres;

--
-- TOC entry 4251 (class 0 OID 0)
-- Dependencies: 349
-- Name: FUNCTION fn_update_emails_timestamp(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_emails_timestamp() IS 'Atualiza o timestamp da coluna updated_at em qualquer update na tabela emails.';


--
-- TOC entry 350 (class 1255 OID 85980)
-- Name: fn_update_establishment_settings_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_establishment_settings_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_establishment_settings_timestamp() OWNER TO postgres;

--
-- TOC entry 4252 (class 0 OID 0)
-- Dependencies: 350
-- Name: FUNCTION fn_update_establishment_settings_timestamp(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_establishment_settings_timestamp() IS 'Atualiza o timestamp da coluna updated_at na tabela establishment_settings.';


--
-- TOC entry 351 (class 1255 OID 85981)
-- Name: fn_update_establishments_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_establishments_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_establishments_timestamp() OWNER TO postgres;

--
-- TOC entry 4253 (class 0 OID 0)
-- Dependencies: 351
-- Name: FUNCTION fn_update_establishments_timestamp(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_establishments_timestamp() IS 'Atualiza o timestamp da coluna updated_at em qualquer update na tabela establishments.';


--
-- TOC entry 352 (class 1255 OID 85982)
-- Name: fn_update_menu_paths(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_menu_paths() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    parent_path TEXT;
BEGIN
    -- Se não tem parent, o path é apenas o próprio slug
    IF NEW.parent_id IS NULL THEN
        NEW.path := NEW.slug;
        NEW.level := 0;
    ELSE
        -- Buscar path do parent
        SELECT m.path, m.level + 1
        INTO parent_path, NEW.level
        FROM master.menus m
        WHERE m.id = NEW.parent_id;

        -- Construir path completo
        NEW.path := parent_path || '/' || NEW.slug;
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION master.fn_update_menu_paths() OWNER TO postgres;

--
-- TOC entry 4254 (class 0 OID 0)
-- Dependencies: 352
-- Name: FUNCTION fn_update_menu_paths(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_menu_paths() IS 'Atualiza automaticamente o path completo e nível do menu na hierarquia.';


--
-- TOC entry 353 (class 1255 OID 85983)
-- Name: fn_update_menus_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_menus_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_menus_timestamp() OWNER TO postgres;

--
-- TOC entry 4255 (class 0 OID 0)
-- Dependencies: 353
-- Name: FUNCTION fn_update_menus_timestamp(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_menus_timestamp() IS 'Atualiza o timestamp da coluna updated_at em qualquer update na tabela menus.';


--
-- TOC entry 354 (class 1255 OID 85984)
-- Name: fn_update_password_changed_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_password_changed_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF OLD.password IS DISTINCT FROM NEW.password THEN
        NEW.password_changed_at = NOW();
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION master.fn_update_password_changed_timestamp() OWNER TO postgres;

--
-- TOC entry 4256 (class 0 OID 0)
-- Dependencies: 354
-- Name: FUNCTION fn_update_password_changed_timestamp(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_password_changed_timestamp() IS 'Atualiza o timestamp de mudança de senha quando o campo password é alterado.';


--
-- TOC entry 355 (class 1255 OID 85985)
-- Name: fn_update_people_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_people_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_people_timestamp() OWNER TO postgres;

--
-- TOC entry 356 (class 1255 OID 85986)
-- Name: fn_update_permissions_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_permissions_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_permissions_timestamp() OWNER TO postgres;

--
-- TOC entry 357 (class 1255 OID 85987)
-- Name: fn_update_phones_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_phones_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_phones_timestamp() OWNER TO postgres;

--
-- TOC entry 4257 (class 0 OID 0)
-- Dependencies: 357
-- Name: FUNCTION fn_update_phones_timestamp(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_phones_timestamp() IS 'Atualiza o timestamp da coluna updated_at em qualquer update na tabela phones.';


--
-- TOC entry 358 (class 1255 OID 85988)
-- Name: fn_update_professionals_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_professionals_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_professionals_timestamp() OWNER TO postgres;

--
-- TOC entry 4258 (class 0 OID 0)
-- Dependencies: 358
-- Name: FUNCTION fn_update_professionals_timestamp(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_professionals_timestamp() IS 'Atualiza o timestamp da coluna updated_at em qualquer update na tabela professionals.';


--
-- TOC entry 359 (class 1255 OID 85989)
-- Name: fn_update_role_permissions_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_role_permissions_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_role_permissions_timestamp() OWNER TO postgres;

--
-- TOC entry 360 (class 1255 OID 85990)
-- Name: fn_update_roles_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_roles_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_roles_timestamp() OWNER TO postgres;

--
-- TOC entry 361 (class 1255 OID 85991)
-- Name: fn_update_tenant_features_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_tenant_features_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_tenant_features_timestamp() OWNER TO postgres;

--
-- TOC entry 362 (class 1255 OID 85992)
-- Name: fn_update_user_contexts_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_user_contexts_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_user_contexts_timestamp() OWNER TO postgres;

--
-- TOC entry 376 (class 1255 OID 87847)
-- Name: fn_update_user_establishments_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_user_establishments_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION master.fn_update_user_establishments_timestamp() OWNER TO postgres;

--
-- TOC entry 363 (class 1255 OID 85993)
-- Name: fn_update_user_roles_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_user_roles_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_user_roles_timestamp() OWNER TO postgres;

--
-- TOC entry 364 (class 1255 OID 85994)
-- Name: fn_update_users_timestamp(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_update_users_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_update_users_timestamp() OWNER TO postgres;

--
-- TOC entry 4259 (class 0 OID 0)
-- Dependencies: 364
-- Name: FUNCTION fn_update_users_timestamp(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_update_users_timestamp() IS 'Atualiza o timestamp da coluna updated_at em qualquer update na tabela users.';


--
-- TOC entry 365 (class 1255 OID 85995)
-- Name: fn_users_password_changed(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_users_password_changed() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
            BEGIN
                IF OLD.password != NEW.password THEN
                    NEW.password_changed_at := CURRENT_TIMESTAMP;
                END IF;
                RETURN NEW;
            END;
            $$;


ALTER FUNCTION master.fn_users_password_changed() OWNER TO postgres;

--
-- TOC entry 366 (class 1255 OID 85996)
-- Name: fn_validate_cnpj(text); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_validate_cnpj(cnpj text) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE
    AS $$
        DECLARE
            cnpj_clean text;
            digit1 integer := 0;
            digit2 integer := 0;
            weights1 integer[] := ARRAY[5,4,3,2,9,8,7,6,5,4,3,2];
            weights2 integer[] := ARRAY[6,5,4,3,2,9,8,7,6,5,4,3,2];
            i integer;
        BEGIN
            -- Remove caracteres especiais
            cnpj_clean := regexp_replace(cnpj, '[^0-9]', '', 'g');

            -- Verifica se tem 14 dígitos
            IF length(cnpj_clean) != 14 THEN
                RETURN false;
            END IF;

            -- Verifica sequências inválidas
            IF cnpj_clean IN ('00000000000000', '11111111111111', '22222222222222') THEN
                RETURN false;
            END IF;

            -- Calcula primeiro dígito
            FOR i IN 1..12 LOOP
                digit1 := digit1 + (substring(cnpj_clean, i, 1)::integer * weights1[i]);
            END LOOP;
            digit1 := digit1 % 11;
            IF digit1 < 2 THEN digit1 := 0; ELSE digit1 := 11 - digit1; END IF;

            -- Calcula segundo dígito
            FOR i IN 1..13 LOOP
                digit2 := digit2 + (substring(cnpj_clean, i, 1)::integer * weights2[i]);
            END LOOP;
            digit2 := digit2 % 11;
            IF digit2 < 2 THEN digit2 := 0; ELSE digit2 := 11 - digit2; END IF;

            RETURN digit1 = substring(cnpj_clean, 13, 1)::integer
               AND digit2 = substring(cnpj_clean, 14, 1)::integer;
        END;
        $$;


ALTER FUNCTION master.fn_validate_cnpj(cnpj text) OWNER TO postgres;

--
-- TOC entry 4260 (class 0 OID 0)
-- Dependencies: 366
-- Name: FUNCTION fn_validate_cnpj(cnpj text); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_validate_cnpj(cnpj text) IS 'Valida os dígitos verificadores de um número de CNPJ.';


--
-- TOC entry 367 (class 1255 OID 85997)
-- Name: fn_validate_coordinates(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_validate_coordinates() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Validar coordenadas do Brasil (aproximadas)
    -- Latitude: -35 a 5 graus
    -- Longitude: -75 a -30 graus
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        IF NEW.latitude < -35 OR NEW.latitude > 5 OR
           NEW.longitude < -75 OR NEW.longitude > -30 THEN
            RAISE EXCEPTION 'Coordenadas fora do território brasileiro: lat=%, lng=%', NEW.latitude, NEW.longitude;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION master.fn_validate_coordinates() OWNER TO postgres;

--
-- TOC entry 4261 (class 0 OID 0)
-- Dependencies: 367
-- Name: FUNCTION fn_validate_coordinates(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_validate_coordinates() IS 'Valida se coordenadas estão dentro dos limites geográficos do Brasil.';


--
-- TOC entry 368 (class 1255 OID 85998)
-- Name: fn_validate_coordinates(numeric, numeric); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_validate_coordinates(lat numeric, lon numeric) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE
    AS $$
        BEGIN
            RETURN lat IS NOT NULL
               AND lon IS NOT NULL
               AND lat BETWEEN -90 AND 90
               AND lon BETWEEN -180 AND 180;
        END;
        $$;


ALTER FUNCTION master.fn_validate_coordinates(lat numeric, lon numeric) OWNER TO postgres;

--
-- TOC entry 369 (class 1255 OID 85999)
-- Name: fn_validate_cpf(text); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_validate_cpf(cpf text) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE
    AS $$
        DECLARE
            cpf_clean text;
            digit1 integer := 0;
            digit2 integer := 0;
            i integer;
        BEGIN
            -- Remove caracteres especiais
            cpf_clean := regexp_replace(cpf, '[^0-9]', '', 'g');

            -- Verifica se tem 11 dígitos
            IF length(cpf_clean) != 11 THEN
                RETURN false;
            END IF;

            -- Verifica sequências inválidas
            IF cpf_clean IN ('00000000000', '11111111111', '22222222222', '33333333333',
                           '44444444444', '55555555555', '66666666666', '77777777777',
                           '88888888888', '99999999999') THEN
                RETURN false;
            END IF;

            -- Calcula primeiro dígito verificador
            FOR i IN 1..9 LOOP
                digit1 := digit1 + (substring(cpf_clean, i, 1)::integer * (11 - i));
            END LOOP;
            digit1 := 11 - (digit1 % 11);
            IF digit1 > 9 THEN digit1 := 0; END IF;

            -- Calcula segundo dígito verificador
            FOR i IN 1..10 LOOP
                digit2 := digit2 + (substring(cpf_clean, i, 1)::integer * (12 - i));
            END LOOP;
            digit2 := 11 - (digit2 % 11);
            IF digit2 > 9 THEN digit2 := 0; END IF;

            -- Verifica se os dígitos calculados conferem
            RETURN digit1 = substring(cpf_clean, 10, 1)::integer
               AND digit2 = substring(cpf_clean, 11, 1)::integer;
        END;
        $$;


ALTER FUNCTION master.fn_validate_cpf(cpf text) OWNER TO postgres;

--
-- TOC entry 4262 (class 0 OID 0)
-- Dependencies: 369
-- Name: FUNCTION fn_validate_cpf(cpf text); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_validate_cpf(cpf text) IS 'Valida os dígitos verificadores de um número de CPF.';


--
-- TOC entry 370 (class 1255 OID 86000)
-- Name: fn_validate_lgpd_consent(bigint, character varying, character varying); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_validate_lgpd_consent(p_person_id bigint, p_purpose character varying, p_data_category character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
        DECLARE
            valid_consent BOOLEAN := false;
        BEGIN
            -- Check if person has valid consent for this purpose/category
            SELECT EXISTS (
                SELECT 1 FROM master.consent_records
                WHERE person_id = p_person_id
                AND status = 'active'
                AND (expires_at IS NULL OR expires_at > NOW())
                AND (
                    consent_type = 'data_processing'
                    OR purpose ILIKE '%' || p_purpose || '%'
                )
                AND (
                    data_categories IS NULL
                    OR data_categories @> jsonb_build_array(p_data_category)
                )
            ) INTO valid_consent;

            RETURN valid_consent;
        END;
        $$;


ALTER FUNCTION master.fn_validate_lgpd_consent(p_person_id bigint, p_purpose character varying, p_data_category character varying) OWNER TO postgres;

--
-- TOC entry 371 (class 1255 OID 86001)
-- Name: fn_validate_menu_hierarchy(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_validate_menu_hierarchy() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            -- Evitar referências circulares
            IF NEW.parent_id IS NOT NULL AND NEW.parent_id = NEW.id THEN
                RAISE EXCEPTION 'Menu cannot be parent of itself';
            END IF;

            RETURN NEW;
        END;
        $$;


ALTER FUNCTION master.fn_validate_menu_hierarchy() OWNER TO postgres;

--
-- TOC entry 4263 (class 0 OID 0)
-- Dependencies: 371
-- Name: FUNCTION fn_validate_menu_hierarchy(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_validate_menu_hierarchy() IS 'Valida hierarquia de menus evitando loops e limitando profundidade.';


--
-- TOC entry 372 (class 1255 OID 86002)
-- Name: fn_validate_phone_format(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_validate_phone_format() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    clean_number VARCHAR(11);
    ddd VARCHAR(2);
BEGIN
    -- Limpar número (remover tudo exceto dígitos)
    clean_number := regexp_replace(NEW.number, '[^0-9]', '', 'g');

    -- Validar comprimento básico
    IF LENGTH(clean_number) NOT BETWEEN 10 AND 11 THEN
        RAISE EXCEPTION 'Número de telefone deve ter 10 ou 11 dígitos. Recebido: % (%)', NEW.number, LENGTH(clean_number);
    END IF;

    -- Extrair DDD
    ddd := LEFT(clean_number, 2);

    -- Validar DDD brasileiro (códigos válidos)
    IF ddd::INTEGER NOT IN (11,12,13,14,15,16,17,18,19,21,22,24,27,28,31,32,33,34,35,37,38,41,42,43,44,45,46,47,48,49,51,53,54,55,61,62,63,64,65,66,67,68,69,71,73,74,75,77,79,81,82,83,84,85,86,87,88,89,91,92,93,94,95,96,97,98,99) THEN
        RAISE EXCEPTION 'DDD inválido: %. Deve ser um DDD brasileiro válido.', ddd;
    END IF;

    -- Atualizar número limpo
    NEW.number := clean_number;

    -- Auto-detectar tipo baseado no comprimento
    IF LENGTH(clean_number) = 11 THEN
        -- Celular (11 dígitos)
        NEW.type := COALESCE(NEW.type, 'mobile');
    ELSIF LENGTH(clean_number) = 10 THEN
        -- Fixo (10 dígitos)
        NEW.type := COALESCE(NEW.type, 'landline');
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION master.fn_validate_phone_format() OWNER TO postgres;

--
-- TOC entry 4264 (class 0 OID 0)
-- Dependencies: 372
-- Name: FUNCTION fn_validate_phone_format(); Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON FUNCTION master.fn_validate_phone_format() IS 'Valida e limpa formato de telefones brasileiros, auto-detecta tipo mobile/landline.';


--
-- TOC entry 373 (class 1255 OID 86003)
-- Name: fn_validate_phone_format(text); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_validate_phone_format(phone_number text) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE
    AS $_$
        BEGIN
            -- Remove caracteres especiais
            phone_number := regexp_replace(phone_number, '[^0-9]', '', 'g');

            -- Verifica formato brasileiro (10 ou 11 dígitos)
            RETURN length(phone_number) IN (10, 11) AND phone_number ~ '^[0-9]+$';
        END;
        $_$;


ALTER FUNCTION master.fn_validate_phone_format(phone_number text) OWNER TO postgres;

--
-- TOC entry 374 (class 1255 OID 86004)
-- Name: fn_validate_role_permissions(bigint); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_validate_role_permissions(p_role_id bigint) RETURNS TABLE(issue_type character varying, issue_description text, permission_name character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Verificar permissões órfãs (papel ou permissão inativa)
    RETURN QUERY
    SELECT
        'inactive_role'::VARCHAR(50) as issue_type,
        'Papel está inativo mas tem permissões atribuídas'::TEXT as issue_description,
        p.name as permission_name
    FROM master.role_permissions rp
    JOIN master.permissions p ON rp.permission_id = p.id
    JOIN master.roles r ON rp.role_id = r.id
    WHERE rp.role_id = p_role_id
    AND r.is_active = false;

    RETURN QUERY
    SELECT
        'inactive_permission'::VARCHAR(50) as issue_type,
        'Permissão está inativa mas está atribuída ao papel'::TEXT as issue_description,
        p.name as permission_name
    FROM master.role_permissions rp
    JOIN master.permissions p ON rp.permission_id = p.id
    WHERE rp.role_id = p_role_id
    AND p.is_active = false;

    -- Verificar conflitos de contexto
    RETURN QUERY
    SELECT
        'context_conflict'::VARCHAR(50) as issue_type,
        'Permissão de nível superior atribuída a papel de nível inferior'::TEXT as issue_description,
        p.name as permission_name
    FROM master.role_permissions rp
    JOIN master.permissions p ON rp.permission_id = p.id
    JOIN master.roles r ON rp.role_id = r.id
    WHERE rp.role_id = p_role_id
    AND (
        (r.context_type = 'establishment' AND p.context_level IN ('system', 'company')) OR
        (r.context_type = 'company' AND p.context_level = 'system')
    );
END;
$$;


ALTER FUNCTION master.fn_validate_role_permissions(p_role_id bigint) OWNER TO postgres;

--
-- TOC entry 375 (class 1255 OID 86005)
-- Name: fn_validate_user_role_context(); Type: FUNCTION; Schema: master; Owner: postgres
--

CREATE FUNCTION master.fn_validate_user_role_context() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    role_context VARCHAR(20);
BEGIN
    SELECT context_type INTO role_context FROM master.roles WHERE id = NEW.role_id;

    IF role_context = 'system' AND NEW.context_type != 'system' THEN
        RAISE EXCEPTION 'Papel de sistema só pode ser atribuído no contexto system';
    END IF;

    IF role_context = 'company' AND NEW.context_type NOT IN ('system', 'company') THEN
        RAISE EXCEPTION 'Papel de empresa só pode ser atribuído nos contextos system ou company';
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION master.fn_validate_user_role_context() OWNER TO postgres;

--
-- TOC entry 288 (class 1259 OID 94185)
-- Name: activity_logs_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.activity_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.activity_logs_id_seq OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 216 (class 1259 OID 86006)
-- Name: activity_logs; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.activity_logs (
    id bigint DEFAULT nextval('master.activity_logs_id_seq'::regclass) NOT NULL,
    log_name character varying(255),
    description text NOT NULL,
    subject_type character varying(255),
    subject_id bigint,
    event character varying(255),
    causer_type character varying(255),
    causer_id bigint,
    context_type character varying(20),
    context_id bigint,
    properties jsonb,
    batch_uuid uuid,
    created_at timestamp(0) without time zone NOT NULL,
    ip_address character varying(45),
    session_id character varying(255),
    business_justification text,
    data_sensitivity_level character varying(255),
    processing_lawful_basis character varying(255),
    user_agent text,
    geographic_location character varying(100),
    CONSTRAINT activity_logs_data_sensitivity_level_check CHECK (((data_sensitivity_level)::text = ANY (ARRAY[('public'::character varying)::text, ('internal'::character varying)::text, ('confidential'::character varying)::text, ('sensitive_personal'::character varying)::text, ('highly_sensitive'::character varying)::text]))),
    CONSTRAINT activity_logs_processing_lawful_basis_check CHECK (((processing_lawful_basis)::text = ANY (ARRAY[('consent'::character varying)::text, ('contract'::character varying)::text, ('legal_obligation'::character varying)::text, ('vital_interests'::character varying)::text, ('public_task'::character varying)::text, ('legitimate_interests'::character varying)::text, ('credit_protection'::character varying)::text, ('health_protection'::character varying)::text, ('fraud_prevention'::character varying)::text])))
);


ALTER TABLE master.activity_logs OWNER TO postgres;

--
-- TOC entry 4265 (class 0 OID 0)
-- Dependencies: 216
-- Name: TABLE activity_logs; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.activity_logs IS 'Log de auditoria de todas as ações do sistema com particionamento por data.';


--
-- TOC entry 4266 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.subject_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.subject_type IS 'Tipo da entidade afetada pela ação (ex: App\\Models\\People).';


--
-- TOC entry 4267 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.subject_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.subject_id IS 'ID da entidade afetada pela ação.';


--
-- TOC entry 4268 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.causer_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.causer_type IS 'Tipo da entidade que causou a ação (ex: App\\Models\\User).';


--
-- TOC entry 4269 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.causer_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.causer_id IS 'ID da entidade que causou a ação. Refere-se a master.users(id) se causer_type for de usuário.';


--
-- TOC entry 4270 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.context_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.context_type IS 'Contexto onde a ação ocorreu (company, establishment).';


--
-- TOC entry 4271 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.context_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.context_id IS 'ID do contexto onde a ação ocorreu.';


--
-- TOC entry 4272 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.properties; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.properties IS 'Propriedades adicionais da ação, como valores antigos e novos.';


--
-- TOC entry 4273 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.ip_address; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.ip_address IS 'IP de origem da operação (obrigatório ANPD 2025)';


--
-- TOC entry 4274 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.session_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.session_id IS 'ID da sessão Laravel para rastreamento';


--
-- TOC entry 4275 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.business_justification; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.business_justification IS 'Justificativa de negócio da operação';


--
-- TOC entry 4276 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.data_sensitivity_level; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.data_sensitivity_level IS 'Nível de sensibilidade dos dados afetados';


--
-- TOC entry 4277 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.processing_lawful_basis; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.processing_lawful_basis IS 'Base legal para processamento (Art. 7º LGPD)';


--
-- TOC entry 4278 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.user_agent; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.user_agent IS 'User agent do navegador/sistema';


--
-- TOC entry 4279 (class 0 OID 0)
-- Dependencies: 216
-- Name: COLUMN activity_logs.geographic_location; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.activity_logs.geographic_location IS 'Localização geográfica da operação';


--
-- TOC entry 217 (class 1259 OID 86013)
-- Name: activity_logs_2025_08; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.activity_logs_2025_08 (
    id bigint NOT NULL,
    log_name character varying(255),
    description text NOT NULL,
    subject_type character varying(255),
    subject_id bigint,
    event character varying(255),
    causer_type character varying(255),
    causer_id bigint,
    context_type character varying(20),
    context_id bigint,
    properties jsonb,
    batch_uuid uuid,
    created_at timestamp(0) without time zone NOT NULL
);


ALTER TABLE master.activity_logs_2025_08 OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 86018)
-- Name: addresses; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.addresses (
    id bigint NOT NULL,
    addressable_type character varying(255) NOT NULL,
    addressable_id bigint NOT NULL,
    type character varying(255) DEFAULT 'residential'::character varying NOT NULL,
    street character varying(255) NOT NULL,
    number character varying(20),
    details character varying(255),
    neighborhood character varying(255) NOT NULL,
    city character varying(255) NOT NULL,
    state character varying(2) NOT NULL,
    zip_code character varying(10) NOT NULL,
    country character varying(2) DEFAULT 'BR'::character varying NOT NULL,
    latitude numeric(10,8),
    longitude numeric(11,8),
    geocoding_accuracy character varying(255),
    geocoding_source character varying(255),
    google_place_id character varying(255),
    formatted_address text,
    ibge_city_code integer,
    ibge_state_code integer,
    region character varying(255),
    microregion character varying(255),
    mesoregion character varying(255),
    area_code character varying(255),
    gia_code character varying(255),
    siafi_code character varying(255),
    quality_score integer,
    is_validated boolean DEFAULT false,
    last_validated_at timestamp(0) without time zone,
    validation_source character varying(255),
    api_data jsonb,
    within_coverage boolean,
    distance_to_establishment integer,
    estimated_travel_time integer,
    access_difficulty character varying(255),
    access_notes text,
    is_principal boolean DEFAULT false,
    is_active boolean DEFAULT true,
    is_confirmed boolean DEFAULT false,
    confirmed_at timestamp(0) without time zone,
    confirmed_by_user_id bigint,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    created_by_user_id bigint,
    updated_by_user_id bigint,
    coordinates_added_at timestamp without time zone,
    coordinates_source character varying(50),
    enriched_at timestamp without time zone,
    enrichment_source character varying(50),
    CONSTRAINT addresses_access_difficulty_check CHECK (((access_difficulty)::text = ANY (ARRAY[('easy'::character varying)::text, ('medium'::character varying)::text, ('hard'::character varying)::text, ('unknown'::character varying)::text]))),
    CONSTRAINT addresses_type_check CHECK (((type)::text = ANY (ARRAY[('residential'::character varying)::text, ('commercial'::character varying)::text, ('correspondence'::character varying)::text, ('billing'::character varying)::text, ('delivery'::character varying)::text, ('other'::character varying)::text])))
);


ALTER TABLE master.addresses OWNER TO postgres;

--
-- TOC entry 4280 (class 0 OID 0)
-- Dependencies: 218
-- Name: TABLE addresses; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.addresses IS 'Tabela polimórfica para endereços de pessoas, empresas e estabelecimentos. Suporta múltiplos endereços por entidade.';


--
-- TOC entry 4281 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.addressable_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.addressable_type IS 'Tipo da entidade (App\Models\Person, App\Models\Company, etc.)';


--
-- TOC entry 4282 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.addressable_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.addressable_id IS 'ID da entidade que possui este endereço';


--
-- TOC entry 4283 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.street; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.street IS 'Logradouro (rua, avenida, etc.)';


--
-- TOC entry 4284 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.number; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.number IS 'Número do imóvel';


--
-- TOC entry 4285 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.details; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.details IS 'Complemento (apartamento, bloco, etc.)';


--
-- TOC entry 4286 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.neighborhood; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.neighborhood IS 'Bairro';


--
-- TOC entry 4287 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.city; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.city IS 'Cidade';


--
-- TOC entry 4288 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.state; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.state IS 'Estado (sigla UF)';


--
-- TOC entry 4289 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.zip_code; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.zip_code IS 'CEP';


--
-- TOC entry 4290 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.country; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.country IS 'País (código ISO)';


--
-- TOC entry 4291 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.quality_score; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.quality_score IS 'Score de qualidade do endereço (0-100)';


--
-- TOC entry 4292 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.api_data; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.api_data IS 'Dados brutos das APIs de geolocalização';


--
-- TOC entry 4293 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.distance_to_establishment; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.distance_to_establishment IS 'Distância em metros';


--
-- TOC entry 4294 (class 0 OID 0)
-- Dependencies: 218
-- Name: COLUMN addresses.estimated_travel_time; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.addresses.estimated_travel_time IS 'Tempo estimado em minutos';


--
-- TOC entry 276 (class 1259 OID 87784)
-- Name: addresses_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.addresses_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.addresses_id_seq OWNER TO postgres;

--
-- TOC entry 4295 (class 0 OID 0)
-- Dependencies: 276
-- Name: addresses_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.addresses_id_seq OWNED BY master.addresses.id;


--
-- TOC entry 289 (class 1259 OID 94188)
-- Name: alembic_version; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE master.alembic_version OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 86032)
-- Name: cache; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.cache (
    key character varying(255) NOT NULL,
    value text NOT NULL,
    expiration integer NOT NULL
);


ALTER TABLE master.cache OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 86037)
-- Name: cache_locks; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.cache_locks (
    key character varying(255) NOT NULL,
    owner character varying(255) NOT NULL,
    expiration integer NOT NULL
);


ALTER TABLE master.cache_locks OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 86042)
-- Name: clients; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.clients (
    id bigint NOT NULL,
    person_id bigint NOT NULL,
    establishment_id bigint NOT NULL,
    client_code character varying(50),
    status character varying(255) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    CONSTRAINT clients_status_check CHECK (((status)::text = ANY (ARRAY[('active'::character varying)::text, ('inactive'::character varying)::text, ('on_hold'::character varying)::text, ('archived'::character varying)::text])))
);


ALTER TABLE master.clients OWNER TO postgres;

--
-- TOC entry 4296 (class 0 OID 0)
-- Dependencies: 221
-- Name: TABLE clients; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.clients IS 'Tabela de "Papel". Define o vínculo de uma entidade da tabela "people" como um cliente de um estabelecimento.';


--
-- TOC entry 4297 (class 0 OID 0)
-- Dependencies: 221
-- Name: COLUMN clients.person_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.clients.person_id IS 'Referência (FK) para o registro na tabela "people" que representa este cliente.';


--
-- TOC entry 4298 (class 0 OID 0)
-- Dependencies: 221
-- Name: COLUMN clients.establishment_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.clients.establishment_id IS 'Referência (FK) para o estabelecimento ao qual o cliente pertence.';


--
-- TOC entry 4299 (class 0 OID 0)
-- Dependencies: 221
-- Name: COLUMN clients.client_code; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.clients.client_code IS 'Código único do cliente dentro do estabelecimento (opcional).';


--
-- TOC entry 4300 (class 0 OID 0)
-- Dependencies: 221
-- Name: COLUMN clients.status; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.clients.status IS 'Status do cliente no estabelecimento: active, inactive, on_hold, archived.';


--
-- TOC entry 277 (class 1259 OID 87786)
-- Name: clients_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.clients_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.clients_id_seq OWNER TO postgres;

--
-- TOC entry 4301 (class 0 OID 0)
-- Dependencies: 277
-- Name: clients_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.clients_id_seq OWNED BY master.clients.id;


--
-- TOC entry 222 (class 1259 OID 86048)
-- Name: companies; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.companies (
    id bigint NOT NULL,
    person_id bigint NOT NULL,
    settings jsonb,
    metadata jsonb,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    display_order integer DEFAULT 0 NOT NULL
);


ALTER TABLE master.companies OWNER TO postgres;

--
-- TOC entry 4302 (class 0 OID 0)
-- Dependencies: 222
-- Name: TABLE companies; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.companies IS 'Tabela de "Papel". Define quais registros da tabela "people" são empresas clientes do sistema Pro Team Care.';


--
-- TOC entry 4303 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN companies.person_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.companies.person_id IS 'Referência (FK) para o registro correspondente na tabela "people" (deve ser do tipo "PJ").';


--
-- TOC entry 4304 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN companies.settings; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.companies.settings IS 'Configurações específicas da empresa DENTRO do sistema Pro Team Care.';


--
-- TOC entry 4305 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN companies.metadata; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.companies.metadata IS 'Dados adicionais flexíveis sobre o status da empresa como cliente.';


--
-- TOC entry 278 (class 1259 OID 87788)
-- Name: companies_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.companies_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.companies_id_seq OWNER TO postgres;

--
-- TOC entry 4306 (class 0 OID 0)
-- Dependencies: 278
-- Name: companies_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.companies_id_seq OWNED BY master.companies.id;


--
-- TOC entry 223 (class 1259 OID 86054)
-- Name: company_settings; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.company_settings (
    id bigint NOT NULL,
    company_id bigint NOT NULL,
    setting_key character varying(100) NOT NULL,
    setting_category character varying(50) NOT NULL,
    setting_value jsonb,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    updated_by_user_id bigint
);


ALTER TABLE master.company_settings OWNER TO postgres;

--
-- TOC entry 4307 (class 0 OID 0)
-- Dependencies: 223
-- Name: TABLE company_settings; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.company_settings IS 'Configurações específicas por empresa no sistema multi-tenant (modelo EAV).';


--
-- TOC entry 4308 (class 0 OID 0)
-- Dependencies: 223
-- Name: COLUMN company_settings.company_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.company_settings.company_id IS 'ID da empresa proprietária da configuração.';


--
-- TOC entry 4309 (class 0 OID 0)
-- Dependencies: 223
-- Name: COLUMN company_settings.setting_key; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.company_settings.setting_key IS 'Chave única da configuração (ex: notification.email.enabled).';


--
-- TOC entry 4310 (class 0 OID 0)
-- Dependencies: 223
-- Name: COLUMN company_settings.setting_category; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.company_settings.setting_category IS 'Categoria da configuração (ex: notification, security, ui).';


--
-- TOC entry 4311 (class 0 OID 0)
-- Dependencies: 223
-- Name: COLUMN company_settings.setting_value; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.company_settings.setting_value IS 'Valor atual da configuração em formato JSONB.';


--
-- TOC entry 224 (class 1259 OID 86060)
-- Name: consent_records; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.consent_records (
    id bigint NOT NULL,
    person_id bigint NOT NULL,
    consent_type character varying(255) NOT NULL,
    purpose character varying(500) NOT NULL,
    data_categories jsonb NOT NULL,
    status character varying(255) DEFAULT 'active'::character varying NOT NULL,
    consent_text text NOT NULL,
    version character varying(10) DEFAULT '1.0'::character varying NOT NULL,
    collection_method character varying(50) NOT NULL,
    given_at timestamp(0) without time zone DEFAULT now() NOT NULL,
    expires_at timestamp(0) without time zone,
    withdrawn_at timestamp(0) without time zone,
    evidence_data jsonb,
    checksum character varying(64),
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    processing_purposes jsonb,
    is_explicit_consent boolean DEFAULT false NOT NULL,
    collection_interface character varying(100),
    withdrawal_reason text,
    withdrawn_by_user_id bigint,
    legal_basis_documentation text,
    CONSTRAINT consent_records_consent_type_check CHECK (((consent_type)::text = ANY (ARRAY[('data_processing'::character varying)::text, ('marketing'::character varying)::text, ('analytics'::character varying)::text, ('third_party_sharing'::character varying)::text, ('health_data'::character varying)::text]))),
    CONSTRAINT consent_records_status_check CHECK (((status)::text = ANY (ARRAY[('active'::character varying)::text, ('withdrawn'::character varying)::text, ('expired'::character varying)::text, ('superseded'::character varying)::text])))
);


ALTER TABLE master.consent_records OWNER TO postgres;

--
-- TOC entry 4312 (class 0 OID 0)
-- Dependencies: 224
-- Name: TABLE consent_records; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.consent_records IS 'Registros de consentimento para compliance LGPD/GDPR.';


--
-- TOC entry 4313 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN consent_records.person_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.consent_records.person_id IS 'ID do titular dos dados na tabela "people".';


--
-- TOC entry 4314 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN consent_records.consent_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.consent_records.consent_type IS 'Tipo de consentimento: data_processing, marketing, etc.';


--
-- TOC entry 4315 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN consent_records.purpose; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.consent_records.purpose IS 'Finalidade específica do consentimento.';


--
-- TOC entry 4316 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN consent_records.data_categories; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.consent_records.data_categories IS 'Categorias de dados cobertas pelo consentimento.';


--
-- TOC entry 4317 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN consent_records.status; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.consent_records.status IS 'Status: active, withdrawn, expired, superseded.';


--
-- TOC entry 4318 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN consent_records.checksum; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.consent_records.checksum IS 'Hash de verificação da integridade do consentimento.';


--
-- TOC entry 4319 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN consent_records.processing_purposes; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.consent_records.processing_purposes IS 'Finalidades específicas do consentimento';


--
-- TOC entry 4320 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN consent_records.is_explicit_consent; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.consent_records.is_explicit_consent IS 'Consentimento explícito';


--
-- TOC entry 4321 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN consent_records.collection_interface; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.consent_records.collection_interface IS 'Interface de coleta (web, app, presencial)';


--
-- TOC entry 4322 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN consent_records.withdrawal_reason; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.consent_records.withdrawal_reason IS 'Motivo da revogação';


--
-- TOC entry 4323 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN consent_records.withdrawn_by_user_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.consent_records.withdrawn_by_user_id IS 'Usuário que processou a revogação';


--
-- TOC entry 4324 (class 0 OID 0)
-- Dependencies: 224
-- Name: COLUMN consent_records.legal_basis_documentation; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.consent_records.legal_basis_documentation IS 'Documentação da base legal';


--
-- TOC entry 225 (class 1259 OID 86072)
-- Name: data_privacy_logs; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.data_privacy_logs (
    id bigint NOT NULL,
    operation_type character varying(50) NOT NULL,
    data_category character varying(50) NOT NULL,
    person_id bigint NOT NULL,
    operator_id bigint,
    context_type character varying(20),
    context_id bigint,
    purpose character varying(200) NOT NULL,
    legal_basis character varying(50) NOT NULL,
    data_fields json,
    is_sensitive_data boolean DEFAULT false NOT NULL,
    consent_id bigint,
    created_at timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    compliance_notes text
);


ALTER TABLE master.data_privacy_logs OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 86079)
-- Name: data_privacy_logs_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.data_privacy_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.data_privacy_logs_id_seq OWNER TO postgres;

--
-- TOC entry 4325 (class 0 OID 0)
-- Dependencies: 226
-- Name: data_privacy_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.data_privacy_logs_id_seq OWNED BY master.data_privacy_logs.id;


--
-- TOC entry 227 (class 1259 OID 86080)
-- Name: documents; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.documents (
    id bigint NOT NULL,
    documentable_type character varying(255) NOT NULL,
    documentable_id bigint NOT NULL,
    type character varying(255) NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    filename character varying(255) NOT NULL,
    original_filename character varying(255) NOT NULL,
    mime_type character varying(100) NOT NULL,
    file_size_bytes bigint NOT NULL,
    file_path character varying(500) NOT NULL,
    file_hash_sha256 character varying(64) NOT NULL,
    category character varying(50),
    tags jsonb,
    is_public boolean DEFAULT false,
    is_required boolean DEFAULT false,
    expires_at timestamp(0) without time zone,
    contains_personal_data boolean DEFAULT false,
    data_retention_expires_at timestamp(0) without time zone,
    uploaded_by_user_id bigint,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    CONSTRAINT documents_documentable_type_check CHECK (((documentable_type)::text = ANY (ARRAY[('App\Models\Company'::character varying)::text, ('App\Models\Establishment'::character varying)::text, ('App\Models\Professional'::character varying)::text, ('App\Models\People'::character varying)::text]))),
    CONSTRAINT documents_type_check CHECK (((type)::text = ANY (ARRAY[('cnpj'::character varying)::text, ('contrato_social'::character varying)::text, ('inscricao_estadual'::character varying)::text, ('inscricao_municipal'::character varying)::text, ('cpf'::character varying)::text, ('rg'::character varying)::text, ('photo'::character varying)::text, ('diploma'::character varying)::text, ('certificate'::character varying)::text, ('cnh'::character varying)::text, ('alvara'::character varying)::text, ('licenca'::character varying)::text, ('procuracao'::character varying)::text, ('contract'::character varying)::text, ('proposal'::character varying)::text, ('budget'::character varying)::text, ('invoice'::character varying)::text, ('report'::character varying)::text, ('medical_report'::character varying)::text, ('exam'::character varying)::text, ('prescription'::character varying)::text, ('other'::character varying)::text])))
);


ALTER TABLE master.documents OWNER TO postgres;

--
-- TOC entry 4326 (class 0 OID 0)
-- Dependencies: 227
-- Name: TABLE documents; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.documents IS 'Documentos e anexos polimórficos para as entidades do sistema.';


--
-- TOC entry 4327 (class 0 OID 0)
-- Dependencies: 227
-- Name: COLUMN documents.documentable_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.documents.documentable_type IS 'O nome da classe do modelo proprietário do documento (ex: App\\Models\\Company).';


--
-- TOC entry 4328 (class 0 OID 0)
-- Dependencies: 227
-- Name: COLUMN documents.documentable_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.documents.documentable_id IS 'O ID do registro proprietário do documento.';


--
-- TOC entry 4329 (class 0 OID 0)
-- Dependencies: 227
-- Name: COLUMN documents.type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.documents.type IS 'Tipo do documento: cnpj, cpf, contract, etc.';


--
-- TOC entry 4330 (class 0 OID 0)
-- Dependencies: 227
-- Name: COLUMN documents.file_hash_sha256; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.documents.file_hash_sha256 IS 'Hash SHA-256 do arquivo para verificação de integridade.';


--
-- TOC entry 4331 (class 0 OID 0)
-- Dependencies: 227
-- Name: COLUMN documents.contains_personal_data; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.documents.contains_personal_data IS 'Indica se o documento contém dados pessoais (LGPD).';


--
-- TOC entry 280 (class 1259 OID 87792)
-- Name: documents_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.documents_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.documents_id_seq OWNER TO postgres;

--
-- TOC entry 4332 (class 0 OID 0)
-- Dependencies: 280
-- Name: documents_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.documents_id_seq OWNED BY master.documents.id;


--
-- TOC entry 228 (class 1259 OID 86091)
-- Name: emails; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.emails (
    id bigint NOT NULL,
    emailable_type character varying(255) NOT NULL,
    emailable_id bigint NOT NULL,
    type character varying(255) DEFAULT 'work'::character varying NOT NULL,
    email_address character varying(255) NOT NULL,
    is_principal boolean DEFAULT false,
    is_active boolean DEFAULT true,
    verified_at timestamp(0) without time zone,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    CONSTRAINT emails_type_check CHECK (((type)::text = ANY (ARRAY[('personal'::character varying)::text, ('work'::character varying)::text, ('billing'::character varying)::text, ('contact'::character varying)::text])))
);


ALTER TABLE master.emails OWNER TO postgres;

--
-- TOC entry 4333 (class 0 OID 0)
-- Dependencies: 228
-- Name: TABLE emails; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.emails IS 'Emails polimórficos para as entidades do sistema.';


--
-- TOC entry 4334 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN emails.emailable_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.emails.emailable_type IS 'O nome da classe do modelo proprietário do email (ex: App\\Models\\Company).';


--
-- TOC entry 4335 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN emails.emailable_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.emails.emailable_id IS 'O ID do registro proprietário do email.';


--
-- TOC entry 4336 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN emails.type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.emails.type IS 'Tipo: personal, work (trabalho), billing (faturamento), contact (contato).';


--
-- TOC entry 4337 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN emails.email_address; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.emails.email_address IS 'O endereço de email.';


--
-- TOC entry 4338 (class 0 OID 0)
-- Dependencies: 228
-- Name: COLUMN emails.is_principal; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.emails.is_principal IS 'Indica se é o email principal da entidade.';


--
-- TOC entry 275 (class 1259 OID 87782)
-- Name: emails_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.emails_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.emails_id_seq OWNER TO postgres;

--
-- TOC entry 4339 (class 0 OID 0)
-- Dependencies: 275
-- Name: emails_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.emails_id_seq OWNED BY master.emails.id;


--
-- TOC entry 229 (class 1259 OID 86101)
-- Name: establishment_settings; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.establishment_settings (
    id bigint NOT NULL,
    establishment_id bigint NOT NULL,
    setting_key character varying(100) NOT NULL,
    setting_category character varying(50) NOT NULL,
    setting_name character varying(200) NOT NULL,
    description text,
    setting_value jsonb,
    default_value jsonb,
    data_type character varying(20) DEFAULT 'string'::character varying NOT NULL,
    is_required boolean DEFAULT false,
    is_editable boolean DEFAULT true,
    input_type character varying(30) DEFAULT 'text'::character varying,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    updated_by_user_id bigint
);


ALTER TABLE master.establishment_settings OWNER TO postgres;

--
-- TOC entry 4340 (class 0 OID 0)
-- Dependencies: 229
-- Name: TABLE establishment_settings; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.establishment_settings IS 'Configurações específicas por estabelecimento (modelo EAV), com herança da empresa.';


--
-- TOC entry 4341 (class 0 OID 0)
-- Dependencies: 229
-- Name: COLUMN establishment_settings.establishment_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.establishment_settings.establishment_id IS 'ID do estabelecimento proprietário da configuração.';


--
-- TOC entry 4342 (class 0 OID 0)
-- Dependencies: 229
-- Name: COLUMN establishment_settings.setting_key; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.establishment_settings.setting_key IS 'Chave única da configuração (ex: scheduling.slot_duration).';


--
-- TOC entry 4343 (class 0 OID 0)
-- Dependencies: 229
-- Name: COLUMN establishment_settings.setting_value; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.establishment_settings.setting_value IS 'Valor atual da configuração em formato JSONB. Se nulo, herda da empresa.';


--
-- TOC entry 230 (class 1259 OID 86111)
-- Name: establishments; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.establishments (
    id bigint NOT NULL,
    person_id bigint NOT NULL,
    company_id bigint NOT NULL,
    code character varying(50) NOT NULL,
    type character varying(255) DEFAULT 'filial'::character varying,
    category character varying(100),
    is_active boolean DEFAULT true,
    is_principal boolean DEFAULT false,
    settings jsonb,
    operating_hours jsonb,
    service_areas jsonb,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    CONSTRAINT establishments_type_check CHECK (((type)::text = ANY (ARRAY[('matriz'::character varying)::text, ('filial'::character varying)::text, ('unidade'::character varying)::text])))
);


ALTER TABLE master.establishments OWNER TO postgres;

--
-- TOC entry 4344 (class 0 OID 0)
-- Dependencies: 230
-- Name: TABLE establishments; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.establishments IS 'Tabela de "Papel". Define quais registros da tabela "people" são estabelecimentos vinculados a uma empresa.';


--
-- TOC entry 4345 (class 0 OID 0)
-- Dependencies: 230
-- Name: COLUMN establishments.person_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.establishments.person_id IS 'Referência (FK) para a identidade do estabelecimento na tabela "people" (deve ser do tipo "PJ").';


--
-- TOC entry 4346 (class 0 OID 0)
-- Dependencies: 230
-- Name: COLUMN establishments.company_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.establishments.company_id IS 'Referência (FK) para a empresa mãe na tabela "companies".';


--
-- TOC entry 4347 (class 0 OID 0)
-- Dependencies: 230
-- Name: COLUMN establishments.code; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.establishments.code IS 'Código único do estabelecimento dentro da empresa.';


--
-- TOC entry 4348 (class 0 OID 0)
-- Dependencies: 230
-- Name: COLUMN establishments.is_principal; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.establishments.is_principal IS 'Indica se é o estabelecimento principal (matriz) da empresa.';


--
-- TOC entry 279 (class 1259 OID 87790)
-- Name: establishments_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.establishments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.establishments_id_seq OWNER TO postgres;

--
-- TOC entry 4349 (class 0 OID 0)
-- Dependencies: 279
-- Name: establishments_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.establishments_id_seq OWNED BY master.establishments.id;


--
-- TOC entry 231 (class 1259 OID 86121)
-- Name: failed_jobs; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.failed_jobs (
    id bigint NOT NULL,
    uuid character varying(255) NOT NULL,
    connection text NOT NULL,
    queue text NOT NULL,
    payload text NOT NULL,
    exception text NOT NULL,
    failed_at timestamp(0) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE master.failed_jobs OWNER TO postgres;

--
-- TOC entry 4350 (class 0 OID 0)
-- Dependencies: 231
-- Name: TABLE failed_jobs; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.failed_jobs IS 'Jobs que falharam durante execução.';


--
-- TOC entry 232 (class 1259 OID 86127)
-- Name: failed_jobs_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.failed_jobs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.failed_jobs_id_seq OWNER TO postgres;

--
-- TOC entry 4351 (class 0 OID 0)
-- Dependencies: 232
-- Name: failed_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.failed_jobs_id_seq OWNED BY master.failed_jobs.id;


--
-- TOC entry 233 (class 1259 OID 86128)
-- Name: job_batches; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.job_batches (
    id character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    total_jobs integer NOT NULL,
    pending_jobs integer NOT NULL,
    failed_jobs integer NOT NULL,
    failed_job_ids text NOT NULL,
    options text,
    cancelled_at integer,
    created_at integer NOT NULL,
    finished_at integer
);


ALTER TABLE master.job_batches OWNER TO postgres;

--
-- TOC entry 4352 (class 0 OID 0)
-- Dependencies: 233
-- Name: TABLE job_batches; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.job_batches IS 'Lotes de jobs agrupados do Laravel.';


--
-- TOC entry 234 (class 1259 OID 86133)
-- Name: jobs; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.jobs (
    id bigint NOT NULL,
    queue character varying(255) NOT NULL,
    payload text NOT NULL,
    attempts smallint NOT NULL,
    reserved_at integer,
    available_at integer NOT NULL,
    created_at integer NOT NULL
);


ALTER TABLE master.jobs OWNER TO postgres;

--
-- TOC entry 4353 (class 0 OID 0)
-- Dependencies: 234
-- Name: TABLE jobs; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.jobs IS 'Fila de jobs assíncronos do Laravel.';


--
-- TOC entry 235 (class 1259 OID 86138)
-- Name: jobs_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.jobs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.jobs_id_seq OWNER TO postgres;

--
-- TOC entry 4354 (class 0 OID 0)
-- Dependencies: 235
-- Name: jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.jobs_id_seq OWNED BY master.jobs.id;


--
-- TOC entry 236 (class 1259 OID 86139)
-- Name: lgpd_audit_config; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.lgpd_audit_config (
    id bigint NOT NULL,
    table_name character varying(63) NOT NULL,
    operation character varying(20) NOT NULL,
    audit_enabled boolean DEFAULT true NOT NULL,
    requires_justification boolean DEFAULT false NOT NULL,
    data_sensitivity_level character varying(255) DEFAULT 'internal'::character varying NOT NULL,
    sensitive_columns jsonb,
    retention_days integer DEFAULT 2555 NOT NULL,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    CONSTRAINT lgpd_audit_config_data_sensitivity_level_check CHECK (((data_sensitivity_level)::text = ANY (ARRAY[('public'::character varying)::text, ('internal'::character varying)::text, ('confidential'::character varying)::text, ('sensitive_personal'::character varying)::text, ('highly_sensitive'::character varying)::text])))
);


ALTER TABLE master.lgpd_audit_config OWNER TO postgres;

--
-- TOC entry 4355 (class 0 OID 0)
-- Dependencies: 236
-- Name: TABLE lgpd_audit_config; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.lgpd_audit_config IS 'Configurações de auditoria LGPD por tabela/operação';


--
-- TOC entry 4356 (class 0 OID 0)
-- Dependencies: 236
-- Name: COLUMN lgpd_audit_config.sensitive_columns; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.lgpd_audit_config.sensitive_columns IS 'Colunas consideradas sensíveis';


--
-- TOC entry 4357 (class 0 OID 0)
-- Dependencies: 236
-- Name: COLUMN lgpd_audit_config.retention_days; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.lgpd_audit_config.retention_days IS 'Dias de retenção dos logs (7 anos padrão)';


--
-- TOC entry 237 (class 1259 OID 86149)
-- Name: lgpd_audit_config_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.lgpd_audit_config_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.lgpd_audit_config_id_seq OWNER TO postgres;

--
-- TOC entry 4358 (class 0 OID 0)
-- Dependencies: 237
-- Name: lgpd_audit_config_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.lgpd_audit_config_id_seq OWNED BY master.lgpd_audit_config.id;


--
-- TOC entry 238 (class 1259 OID 86150)
-- Name: lgpd_incidents; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.lgpd_incidents (
    id bigint NOT NULL,
    incident_id character varying(50) NOT NULL,
    occurred_at timestamp(0) with time zone NOT NULL,
    detected_at timestamp(0) with time zone DEFAULT now() NOT NULL,
    incident_type character varying(255) NOT NULL,
    severity character varying(255) NOT NULL,
    affected_subjects_count integer DEFAULT 0 NOT NULL,
    affected_data_categories jsonb NOT NULL,
    involves_sensitive_data boolean DEFAULT false NOT NULL,
    description text NOT NULL,
    root_cause text,
    mitigation_actions text,
    anpd_notified boolean DEFAULT false NOT NULL,
    anpd_notification_at timestamp(0) with time zone,
    subjects_notified boolean DEFAULT false NOT NULL,
    status character varying(255) DEFAULT 'open'::character varying NOT NULL,
    responsible_user_id bigint,
    created_at timestamp(0) without time zone,
    updated_at timestamp(0) without time zone,
    CONSTRAINT lgpd_incidents_incident_type_check CHECK (((incident_type)::text = ANY (ARRAY[('data_breach'::character varying)::text, ('unauthorized_access'::character varying)::text, ('data_loss'::character varying)::text, ('system_compromise'::character varying)::text, ('privacy_violation'::character varying)::text, ('consent_violation'::character varying)::text]))),
    CONSTRAINT lgpd_incidents_severity_check CHECK (((severity)::text = ANY (ARRAY[('low'::character varying)::text, ('medium'::character varying)::text, ('high'::character varying)::text, ('critical'::character varying)::text]))),
    CONSTRAINT lgpd_incidents_status_check CHECK (((status)::text = ANY (ARRAY[('open'::character varying)::text, ('investigating'::character varying)::text, ('resolved'::character varying)::text, ('closed'::character varying)::text])))
);


ALTER TABLE master.lgpd_incidents OWNER TO postgres;

--
-- TOC entry 4359 (class 0 OID 0)
-- Dependencies: 238
-- Name: TABLE lgpd_incidents; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.lgpd_incidents IS 'Registro de incidentes de segurança/privacidade - ANPD Resolution 15/2024';


--
-- TOC entry 4360 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN lgpd_incidents.incident_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.lgpd_incidents.incident_id IS 'ID único do incidente';


--
-- TOC entry 4361 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN lgpd_incidents.occurred_at; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.lgpd_incidents.occurred_at IS 'Data/hora do incidente';


--
-- TOC entry 4362 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN lgpd_incidents.incident_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.lgpd_incidents.incident_type IS 'Tipo de incidente';


--
-- TOC entry 4363 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN lgpd_incidents.severity; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.lgpd_incidents.severity IS 'Severidade do incidente';


--
-- TOC entry 4364 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN lgpd_incidents.affected_data_categories; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.lgpd_incidents.affected_data_categories IS 'Categorias de dados afetados';


--
-- TOC entry 4365 (class 0 OID 0)
-- Dependencies: 238
-- Name: COLUMN lgpd_incidents.description; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.lgpd_incidents.description IS 'Descrição do incidente';


--
-- TOC entry 239 (class 1259 OID 86164)
-- Name: lgpd_incidents_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.lgpd_incidents_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.lgpd_incidents_id_seq OWNER TO postgres;

--
-- TOC entry 4366 (class 0 OID 0)
-- Dependencies: 239
-- Name: lgpd_incidents_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.lgpd_incidents_id_seq OWNED BY master.lgpd_incidents.id;


--
-- TOC entry 240 (class 1259 OID 86165)
-- Name: menus; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.menus (
    id bigint NOT NULL,
    parent_id bigint,
    level integer DEFAULT 0,
    sort_order integer DEFAULT 0,
    name character varying(100) NOT NULL,
    slug character varying(100) NOT NULL,
    path text,
    url character varying(255),
    route_name character varying(100),
    route_params jsonb,
    icon character varying(50),
    color character varying(20),
    description text,
    permission_name character varying(255),
    required_permissions jsonb,
    required_roles jsonb,
    target character varying(255) DEFAULT '_self'::character varying,
    type character varying(255) DEFAULT 'menu'::character varying,
    accepts_children boolean DEFAULT true,
    badge_text character varying(20),
    badge_color character varying(20),
    badge_expression text,
    visible_in_menu boolean DEFAULT true,
    visible_in_breadcrumb boolean DEFAULT true,
    is_featured boolean DEFAULT false,
    company_specific boolean DEFAULT false,
    allowed_companies jsonb,
    establishment_specific boolean DEFAULT false,
    allowed_establishments jsonb,
    metadata jsonb,
    is_active boolean DEFAULT true,
    is_visible boolean DEFAULT true,
    dev_only boolean DEFAULT false,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    created_by_user_id bigint,
    updated_by_user_id bigint,
    CONSTRAINT menus_target_check CHECK (((target)::text = ANY (ARRAY[('_self'::character varying)::text, ('_blank'::character varying)::text, ('_parent'::character varying)::text, ('_top'::character varying)::text]))),
    CONSTRAINT menus_type_check CHECK (((type)::text = ANY (ARRAY[('menu'::character varying)::text, ('divider'::character varying)::text, ('header'::character varying)::text, ('separator'::character varying)::text])))
);


ALTER TABLE master.menus OWNER TO postgres;

--
-- TOC entry 4367 (class 0 OID 0)
-- Dependencies: 240
-- Name: TABLE menus; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.menus IS 'Sistema de menus hierárquicos integrado com RBAC do Spatie Laravel Permission.';


--
-- TOC entry 4368 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.parent_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.parent_id IS 'ID do menu pai (NULL para menus raiz).';


--
-- TOC entry 4369 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.level; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.level IS 'Nível na hierarquia (0=raiz, calculado automaticamente).';


--
-- TOC entry 4370 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.name; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.name IS 'Nome exibido no menu.';


--
-- TOC entry 4371 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.slug; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.slug IS 'Identificador único URL-friendly.';


--
-- TOC entry 4372 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.path; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.path IS 'Caminho completo na hierarquia (ex: cadastros/pessoas/clientes).';


--
-- TOC entry 4373 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.url; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.url IS 'URL absoluta ou relativa do menu.';


--
-- TOC entry 4374 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.route_name; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.route_name IS 'Nome da rota Laravel.';


--
-- TOC entry 4375 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.route_params; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.route_params IS 'Parâmetros da rota em formato JSONB.';


--
-- TOC entry 4376 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.icon; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.icon IS 'Classe CSS do ícone (FontAwesome, Bootstrap Icons, etc).';


--
-- TOC entry 4377 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.permission_name; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.permission_name IS 'Permissão necessária (integração com Spatie Permission).';


--
-- TOC entry 4378 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.required_permissions; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.required_permissions IS 'Múltiplas permissões com operador AND/OR.';


--
-- TOC entry 4379 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.required_roles; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.required_roles IS 'Roles necessárias com operador AND/OR.';


--
-- TOC entry 4380 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.type IS 'Tipo: menu, divider, header, separator.';


--
-- TOC entry 4381 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.badge_text; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.badge_text IS 'Texto do badge/contador no menu.';


--
-- TOC entry 4382 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.company_specific; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.company_specific IS 'Se é específico para certas empresas.';


--
-- TOC entry 4383 (class 0 OID 0)
-- Dependencies: 240
-- Name: COLUMN menus.establishment_specific; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.menus.establishment_specific IS 'Se é específico para estabelecimentos.';


--
-- TOC entry 241 (class 1259 OID 86186)
-- Name: migrations; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.migrations (
    id integer NOT NULL,
    migration character varying(255) NOT NULL,
    batch integer NOT NULL
);


ALTER TABLE master.migrations OWNER TO postgres;

--
-- TOC entry 242 (class 1259 OID 86189)
-- Name: migrations_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.migrations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.migrations_id_seq OWNER TO postgres;

--
-- TOC entry 4384 (class 0 OID 0)
-- Dependencies: 242
-- Name: migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.migrations_id_seq OWNED BY master.migrations.id;


--
-- TOC entry 243 (class 1259 OID 86190)
-- Name: password_reset_tokens; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.password_reset_tokens (
    email character varying(255) NOT NULL,
    token character varying(255) NOT NULL,
    created_at timestamp(0) without time zone
);


ALTER TABLE master.password_reset_tokens OWNER TO postgres;

--
-- TOC entry 4385 (class 0 OID 0)
-- Dependencies: 243
-- Name: TABLE password_reset_tokens; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.password_reset_tokens IS 'Tokens para reset de senha do sistema de autenticação Laravel.';


--
-- TOC entry 244 (class 1259 OID 86195)
-- Name: people; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.people (
    id bigint NOT NULL,
    person_type character varying(255) NOT NULL,
    name character varying(200) NOT NULL,
    trade_name character varying(200),
    tax_id character varying(14) NOT NULL,
    secondary_tax_id character varying(20),
    birth_date date,
    gender character varying(255),
    marital_status character varying(255),
    occupation character varying(100),
    incorporation_date date,
    tax_regime character varying(50),
    legal_nature character varying(100),
    municipal_registration character varying(20),
    status character varying(255) DEFAULT 'active'::character varying,
    is_active boolean DEFAULT true,
    metadata jsonb,
    lgpd_consent_version character varying(10),
    lgpd_consent_given_at timestamp(0) without time zone,
    lgpd_data_retention_expires_at timestamp(0) without time zone,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    website text,
    description text,
    CONSTRAINT people_gender_check CHECK (((gender)::text = ANY (ARRAY[('male'::character varying)::text, ('female'::character varying)::text, ('non_binary'::character varying)::text, ('not_informed'::character varying)::text]))),
    CONSTRAINT people_marital_status_check CHECK (((marital_status)::text = ANY (ARRAY[('single'::character varying)::text, ('married'::character varying)::text, ('divorced'::character varying)::text, ('widowed'::character varying)::text, ('stable_union'::character varying)::text, ('not_informed'::character varying)::text]))),
    CONSTRAINT people_person_type_check CHECK (((person_type)::text = ANY (ARRAY[('PF'::character varying)::text, ('PJ'::character varying)::text]))),
    CONSTRAINT people_status_check CHECK (((status)::text = ANY (ARRAY[('active'::character varying)::text, ('inactive'::character varying)::text, ('pending'::character varying)::text, ('suspended'::character varying)::text, ('blocked'::character varying)::text])))
);


ALTER TABLE master.people OWNER TO postgres;

--
-- TOC entry 4386 (class 0 OID 0)
-- Dependencies: 244
-- Name: TABLE people; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.people IS 'Tabela mestra unificada para entidades Físicas (PF) e Jurídicas (PJ). Fonte única de verdade para dados cadastrais.';


--
-- TOC entry 4387 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN people.person_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.people.person_type IS 'Discriminador de tipo: PF (Pessoa Física) ou PJ (Pessoa Jurídica)';


--
-- TOC entry 4388 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN people.name; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.people.name IS 'Nome completo (se PF) ou Razão Social (se PJ)';


--
-- TOC entry 4389 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN people.trade_name; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.people.trade_name IS 'Nome social (se PF) ou Nome Fantasia (se PJ)';


--
-- TOC entry 4390 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN people.tax_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.people.tax_id IS 'CPF (11 dígitos) ou CNPJ (14 dígitos), sem máscara. Único e validado matematicamente.';


--
-- TOC entry 4391 (class 0 OID 0)
-- Dependencies: 244
-- Name: COLUMN people.secondary_tax_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.people.secondary_tax_id IS 'RG (se PF) ou Inscrição Estadual (se PJ)';


--
-- TOC entry 245 (class 1259 OID 86207)
-- Name: people_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.people_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.people_id_seq OWNER TO postgres;

--
-- TOC entry 4392 (class 0 OID 0)
-- Dependencies: 245
-- Name: people_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.people_id_seq OWNED BY master.people.id;


--
-- TOC entry 246 (class 1259 OID 86208)
-- Name: permissions; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.permissions (
    id bigint NOT NULL,
    name character varying(125) NOT NULL,
    display_name character varying(200) NOT NULL,
    description text,
    module character varying(50) NOT NULL,
    action character varying(50) NOT NULL,
    resource character varying(50) NOT NULL,
    context_level character varying(255) DEFAULT 'establishment'::character varying NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone DEFAULT now(),
    CONSTRAINT permissions_context_level_check CHECK (((context_level)::text = ANY (ARRAY[('system'::character varying)::text, ('company'::character varying)::text, ('establishment'::character varying)::text])))
);


ALTER TABLE master.permissions OWNER TO postgres;

--
-- TOC entry 4393 (class 0 OID 0)
-- Dependencies: 246
-- Name: TABLE permissions; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.permissions IS 'Permissões granulares do sistema RBAC';


--
-- TOC entry 4394 (class 0 OID 0)
-- Dependencies: 246
-- Name: COLUMN permissions.name; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.permissions.name IS 'Nome único da permissão em snake_case';


--
-- TOC entry 4395 (class 0 OID 0)
-- Dependencies: 246
-- Name: COLUMN permissions.module; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.permissions.module IS 'Módulo do sistema (users, companies, reports, etc.)';


--
-- TOC entry 4396 (class 0 OID 0)
-- Dependencies: 246
-- Name: COLUMN permissions.action; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.permissions.action IS 'Ação (view, create, update, delete, etc.)';


--
-- TOC entry 4397 (class 0 OID 0)
-- Dependencies: 246
-- Name: COLUMN permissions.resource; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.permissions.resource IS 'Recurso específico dentro do módulo';


--
-- TOC entry 4398 (class 0 OID 0)
-- Dependencies: 246
-- Name: COLUMN permissions.context_level; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.permissions.context_level IS 'Nível de contexto da permissão';


--
-- TOC entry 247 (class 1259 OID 86218)
-- Name: permissions_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.permissions_id_seq OWNER TO postgres;

--
-- TOC entry 4399 (class 0 OID 0)
-- Dependencies: 247
-- Name: permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.permissions_id_seq OWNED BY master.permissions.id;


--
-- TOC entry 274 (class 1259 OID 87779)
-- Name: phones_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.phones_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.phones_id_seq OWNER TO postgres;

--
-- TOC entry 248 (class 1259 OID 86219)
-- Name: phones; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.phones (
    id bigint DEFAULT nextval('master.phones_id_seq'::regclass) NOT NULL,
    phoneable_type character varying(255) NOT NULL,
    phoneable_id bigint NOT NULL,
    type character varying(255) DEFAULT 'mobile'::character varying NOT NULL,
    country_code character varying(3) DEFAULT '55'::character varying NOT NULL,
    number character varying(11) NOT NULL,
    extension character varying(10),
    is_whatsapp boolean DEFAULT false,
    whatsapp_formatted character varying(15),
    whatsapp_verified boolean DEFAULT false,
    whatsapp_verified_at timestamp(0) without time zone,
    whatsapp_business boolean DEFAULT false,
    whatsapp_name character varying(100),
    accepts_whatsapp_marketing boolean DEFAULT false,
    accepts_whatsapp_notifications boolean DEFAULT true,
    whatsapp_preferred_time_start time(0) without time zone DEFAULT '08:00:00'::time without time zone,
    whatsapp_preferred_time_end time(0) without time zone DEFAULT '18:00:00'::time without time zone,
    phone_name character varying(50),
    carrier character varying(30),
    line_type character varying(255),
    is_principal boolean DEFAULT false,
    is_active boolean DEFAULT true,
    can_receive_calls boolean DEFAULT true,
    can_receive_sms boolean DEFAULT false,
    contact_priority integer DEFAULT 1,
    verified_at timestamp(0) without time zone,
    verification_method character varying(255),
    last_contact_attempt timestamp(0) without time zone,
    last_contact_success timestamp(0) without time zone,
    contact_attempts_count integer DEFAULT 0,
    api_data jsonb,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    created_by_user_id bigint,
    updated_by_user_id bigint,
    CONSTRAINT phones_line_type_check CHECK (((line_type)::text = ANY (ARRAY[('prepaid'::character varying)::text, ('postpaid'::character varying)::text, ('corporate'::character varying)::text]))),
    CONSTRAINT phones_type_check CHECK (((type)::text = ANY (ARRAY[('landline'::character varying)::text, ('mobile'::character varying)::text, ('whatsapp'::character varying)::text, ('commercial'::character varying)::text, ('emergency'::character varying)::text, ('fax'::character varying)::text]))),
    CONSTRAINT phones_verification_method_check CHECK (((verification_method)::text = ANY (ARRAY[('call'::character varying)::text, ('sms'::character varying)::text, ('whatsapp'::character varying)::text, ('manual'::character varying)::text, ('api'::character varying)::text])))
);


ALTER TABLE master.phones OWNER TO postgres;

--
-- TOC entry 4400 (class 0 OID 0)
-- Dependencies: 248
-- Name: TABLE phones; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.phones IS 'Telefones polimórficos com integração completa ao WhatsApp e APIs de validação.';


--
-- TOC entry 4401 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.phoneable_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.phoneable_type IS 'Classe do modelo proprietário do telefone.';


--
-- TOC entry 4402 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.phoneable_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.phoneable_id IS 'ID do registro proprietário do telefone.';


--
-- TOC entry 4403 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.type IS 'Tipo: landline, mobile, whatsapp, commercial, emergency, fax.';


--
-- TOC entry 4404 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.number; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.number IS 'Número limpo (só dígitos): DDD + número (10-11 dígitos).';


--
-- TOC entry 4405 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.is_whatsapp; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.is_whatsapp IS 'Se o número tem WhatsApp ativo.';


--
-- TOC entry 4406 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.whatsapp_formatted; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.whatsapp_formatted IS 'Número formatado para links WhatsApp (+5511999999999).';


--
-- TOC entry 4407 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.whatsapp_verified; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.whatsapp_verified IS 'Se foi verificado via WhatsApp Business API.';


--
-- TOC entry 4408 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.whatsapp_business; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.whatsapp_business IS 'Se é conta WhatsApp Business verificada.';


--
-- TOC entry 4409 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.whatsapp_name; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.whatsapp_name IS 'Nome exibido no WhatsApp Business.';


--
-- TOC entry 4410 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.accepts_whatsapp_marketing; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.accepts_whatsapp_marketing IS 'Aceita receber mensagens de marketing via WhatsApp.';


--
-- TOC entry 4411 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.accepts_whatsapp_notifications; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.accepts_whatsapp_notifications IS 'Aceita notificações de sistema via WhatsApp.';


--
-- TOC entry 4412 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.whatsapp_preferred_time_start; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.whatsapp_preferred_time_start IS 'Horário preferido INÍCIO para receber mensagens.';


--
-- TOC entry 4413 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.whatsapp_preferred_time_end; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.whatsapp_preferred_time_end IS 'Horário preferido FIM para receber mensagens.';


--
-- TOC entry 4414 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.phone_name; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.phone_name IS 'Apelido do telefone (Pessoal, Trabalho, etc.).';


--
-- TOC entry 4415 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.carrier; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.carrier IS 'Operadora: Vivo, Claro, Tim, Oi, etc.';


--
-- TOC entry 4416 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.line_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.line_type IS 'Tipo de linha: prepaid, postpaid, corporate.';


--
-- TOC entry 4417 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.contact_priority; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.contact_priority IS 'Prioridade de contato (1=maior, 10=menor).';


--
-- TOC entry 4418 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.verified_at; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.verified_at IS 'Quando o número foi verificado pela última vez.';


--
-- TOC entry 4419 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.verification_method; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.verification_method IS 'Método de verificação: call, sms, whatsapp, manual, api.';


--
-- TOC entry 4420 (class 0 OID 0)
-- Dependencies: 248
-- Name: COLUMN phones.api_data; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.phones.api_data IS 'Dados completos das APIs de telefone/WhatsApp em JSONB.';


--
-- TOC entry 249 (class 1259 OID 86243)
-- Name: professionals; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.professionals (
    id bigint NOT NULL,
    pf_person_id bigint NOT NULL,
    pj_person_id bigint,
    establishment_id bigint NOT NULL,
    professional_code character varying(50),
    status character varying(255) DEFAULT 'active'::character varying NOT NULL,
    specialties jsonb,
    admission_date date,
    termination_date date,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    CONSTRAINT professionals_status_check CHECK (((status)::text = ANY (ARRAY[('active'::character varying)::text, ('inactive'::character varying)::text, ('on_leave'::character varying)::text, ('suspended'::character varying)::text])))
);


ALTER TABLE master.professionals OWNER TO postgres;

--
-- TOC entry 4421 (class 0 OID 0)
-- Dependencies: 249
-- Name: TABLE professionals; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.professionals IS 'Tabela de "Papel". Define os profissionais de home care, ligando suas identidades PF e PJ (MEI).';


--
-- TOC entry 4422 (class 0 OID 0)
-- Dependencies: 249
-- Name: COLUMN professionals.pf_person_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.professionals.pf_person_id IS 'Referência (FK) obrigatória para a identidade da Pessoa Física na tabela "people".';


--
-- TOC entry 4423 (class 0 OID 0)
-- Dependencies: 249
-- Name: COLUMN professionals.pj_person_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.professionals.pj_person_id IS 'Referência (FK) opcional para a identidade da Pessoa Jurídica (MEI) na tabela "people".';


--
-- TOC entry 4424 (class 0 OID 0)
-- Dependencies: 249
-- Name: COLUMN professionals.establishment_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.professionals.establishment_id IS 'Referência (FK) para o estabelecimento ao qual o profissional está vinculado.';


--
-- TOC entry 4425 (class 0 OID 0)
-- Dependencies: 249
-- Name: COLUMN professionals.specialties; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.professionals.specialties IS 'Lista de especialidades do profissional em formato JSONB.';


--
-- TOC entry 281 (class 1259 OID 87794)
-- Name: professionals_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.professionals_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.professionals_id_seq OWNER TO postgres;

--
-- TOC entry 4426 (class 0 OID 0)
-- Dependencies: 281
-- Name: professionals_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.professionals_id_seq OWNED BY master.professionals.id;


--
-- TOC entry 250 (class 1259 OID 86251)
-- Name: query_audit_logs; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.query_audit_logs (
    id bigint NOT NULL,
    "timestamp" timestamp(0) with time zone DEFAULT now() NOT NULL,
    user_id bigint NOT NULL,
    ip_address character varying(45) NOT NULL,
    session_id character varying(255),
    table_accessed character varying(63) NOT NULL,
    records_accessed jsonb,
    records_count integer DEFAULT 0 NOT NULL,
    query_purpose text NOT NULL,
    lawful_basis character varying(255) NOT NULL,
    data_sensitivity_level character varying(255) NOT NULL,
    access_context character varying(200),
    application_module character varying(100),
    CONSTRAINT query_audit_logs_data_sensitivity_level_check CHECK (((data_sensitivity_level)::text = ANY (ARRAY[('public'::character varying)::text, ('internal'::character varying)::text, ('confidential'::character varying)::text, ('sensitive_personal'::character varying)::text, ('highly_sensitive'::character varying)::text]))),
    CONSTRAINT query_audit_logs_lawful_basis_check CHECK (((lawful_basis)::text = ANY (ARRAY[('consent'::character varying)::text, ('contract'::character varying)::text, ('legal_obligation'::character varying)::text, ('vital_interests'::character varying)::text, ('public_task'::character varying)::text, ('legitimate_interests'::character varying)::text, ('credit_protection'::character varying)::text])))
);


ALTER TABLE master.query_audit_logs OWNER TO postgres;

--
-- TOC entry 4427 (class 0 OID 0)
-- Dependencies: 250
-- Name: TABLE query_audit_logs; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.query_audit_logs IS 'Logs de auditoria para consultas (SELECT) - Obrigatório ANPD 2025';


--
-- TOC entry 4428 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN query_audit_logs.user_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.query_audit_logs.user_id IS 'Usuário que executou a consulta';


--
-- TOC entry 4429 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN query_audit_logs.ip_address; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.query_audit_logs.ip_address IS 'IP de origem';


--
-- TOC entry 4430 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN query_audit_logs.table_accessed; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.query_audit_logs.table_accessed IS 'Tabela consultada';


--
-- TOC entry 4431 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN query_audit_logs.records_accessed; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.query_audit_logs.records_accessed IS 'IDs dos registros acessados';


--
-- TOC entry 4432 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN query_audit_logs.records_count; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.query_audit_logs.records_count IS 'Quantidade de registros retornados';


--
-- TOC entry 4433 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN query_audit_logs.query_purpose; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.query_audit_logs.query_purpose IS 'Finalidade da consulta';


--
-- TOC entry 4434 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN query_audit_logs.lawful_basis; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.query_audit_logs.lawful_basis IS 'Base legal da consulta';


--
-- TOC entry 4435 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN query_audit_logs.data_sensitivity_level; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.query_audit_logs.data_sensitivity_level IS 'Nível de sensibilidade dos dados consultados';


--
-- TOC entry 4436 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN query_audit_logs.access_context; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.query_audit_logs.access_context IS 'Contexto da consulta (tela, relatório, etc)';


--
-- TOC entry 4437 (class 0 OID 0)
-- Dependencies: 250
-- Name: COLUMN query_audit_logs.application_module; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.query_audit_logs.application_module IS 'Módulo do sistema';


--
-- TOC entry 251 (class 1259 OID 86260)
-- Name: query_audit_logs_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.query_audit_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.query_audit_logs_id_seq OWNER TO postgres;

--
-- TOC entry 4438 (class 0 OID 0)
-- Dependencies: 251
-- Name: query_audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.query_audit_logs_id_seq OWNED BY master.query_audit_logs.id;


--
-- TOC entry 252 (class 1259 OID 86261)
-- Name: role_permissions; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.role_permissions (
    id bigint NOT NULL,
    role_id bigint NOT NULL,
    permission_id bigint NOT NULL,
    granted_by_user_id bigint,
    granted_at timestamp(0) without time zone DEFAULT now()
);


ALTER TABLE master.role_permissions OWNER TO postgres;

--
-- TOC entry 4439 (class 0 OID 0)
-- Dependencies: 252
-- Name: TABLE role_permissions; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.role_permissions IS 'Relacionamento N:M entre papéis e permissões';


--
-- TOC entry 4440 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN role_permissions.role_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.role_permissions.role_id IS 'ID do papel que recebe a permissão';


--
-- TOC entry 4441 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN role_permissions.permission_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.role_permissions.permission_id IS 'ID da permissão concedida';


--
-- TOC entry 4442 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN role_permissions.granted_by_user_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.role_permissions.granted_by_user_id IS 'ID do usuário que concedeu a permissão';


--
-- TOC entry 4443 (class 0 OID 0)
-- Dependencies: 252
-- Name: COLUMN role_permissions.granted_at; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.role_permissions.granted_at IS 'Data/hora da concessão da permissão';


--
-- TOC entry 253 (class 1259 OID 86265)
-- Name: role_permissions_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.role_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.role_permissions_id_seq OWNER TO postgres;

--
-- TOC entry 4444 (class 0 OID 0)
-- Dependencies: 253
-- Name: role_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.role_permissions_id_seq OWNED BY master.role_permissions.id;


--
-- TOC entry 254 (class 1259 OID 86266)
-- Name: roles; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.roles (
    id bigint NOT NULL,
    name character varying(125) NOT NULL,
    display_name character varying(200) NOT NULL,
    description text,
    level integer DEFAULT 0 NOT NULL,
    context_type character varying(255) DEFAULT 'establishment'::character varying NOT NULL,
    is_active boolean DEFAULT true,
    is_system_role boolean DEFAULT false,
    settings jsonb,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone DEFAULT now(),
    CONSTRAINT roles_context_type_check CHECK (((context_type)::text = ANY (ARRAY[('system'::character varying)::text, ('company'::character varying)::text, ('establishment'::character varying)::text])))
);


ALTER TABLE master.roles OWNER TO postgres;

--
-- TOC entry 4445 (class 0 OID 0)
-- Dependencies: 254
-- Name: TABLE roles; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.roles IS 'Papéis/funções do sistema RBAC';


--
-- TOC entry 4446 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN roles.name; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.roles.name IS 'Nome único do papel em snake_case';


--
-- TOC entry 4447 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN roles.display_name; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.roles.display_name IS 'Nome amigável para exibição';


--
-- TOC entry 4448 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN roles.level; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.roles.level IS 'Nível hierárquico do papel (0-100)';


--
-- TOC entry 4449 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN roles.context_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.roles.context_type IS 'Contexto do papel: system, company, establishment';


--
-- TOC entry 4450 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN roles.is_system_role; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.roles.is_system_role IS 'Indica se é um papel padrão do sistema';


--
-- TOC entry 4451 (class 0 OID 0)
-- Dependencies: 254
-- Name: COLUMN roles.settings; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.roles.settings IS 'Configurações específicas do papel';


--
-- TOC entry 255 (class 1259 OID 86278)
-- Name: roles_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.roles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.roles_id_seq OWNER TO postgres;

--
-- TOC entry 4452 (class 0 OID 0)
-- Dependencies: 255
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.roles_id_seq OWNED BY master.roles.id;


--
-- TOC entry 256 (class 1259 OID 86279)
-- Name: sessions; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.sessions (
    id character varying(255) NOT NULL,
    user_id bigint,
    ip_address inet,
    user_agent text,
    payload text NOT NULL,
    last_activity integer NOT NULL
);


ALTER TABLE master.sessions OWNER TO postgres;

--
-- TOC entry 257 (class 1259 OID 86284)
-- Name: tenant_features; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.tenant_features (
    id bigint NOT NULL,
    tenant_type character varying(255) NOT NULL,
    tenant_id bigint NOT NULL,
    feature_key character varying(100) NOT NULL,
    is_enabled boolean DEFAULT true,
    usage_limit integer,
    current_usage integer DEFAULT 0,
    feature_config jsonb,
    enabled_at timestamp(0) without time zone DEFAULT now(),
    expires_at timestamp(0) without time zone,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    updated_by_user_id bigint,
    CONSTRAINT tenant_features_tenant_type_check CHECK (((tenant_type)::text = ANY (ARRAY[('company'::character varying)::text, ('establishment'::character varying)::text])))
);


ALTER TABLE master.tenant_features OWNER TO postgres;

--
-- TOC entry 4453 (class 0 OID 0)
-- Dependencies: 257
-- Name: TABLE tenant_features; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.tenant_features IS 'Controle de funcionalidades habilitadas por empresa/estabelecimento.';


--
-- TOC entry 4454 (class 0 OID 0)
-- Dependencies: 257
-- Name: COLUMN tenant_features.tenant_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.tenant_features.tenant_type IS 'Tipo do tenant: company ou establishment.';


--
-- TOC entry 4455 (class 0 OID 0)
-- Dependencies: 257
-- Name: COLUMN tenant_features.tenant_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.tenant_features.tenant_id IS 'ID da empresa ou estabelecimento.';


--
-- TOC entry 4456 (class 0 OID 0)
-- Dependencies: 257
-- Name: COLUMN tenant_features.feature_key; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.tenant_features.feature_key IS 'Chave única da funcionalidade (ex: scheduling.advanced).';


--
-- TOC entry 4457 (class 0 OID 0)
-- Dependencies: 257
-- Name: COLUMN tenant_features.is_enabled; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.tenant_features.is_enabled IS 'Se a funcionalidade está habilitada.';


--
-- TOC entry 4458 (class 0 OID 0)
-- Dependencies: 257
-- Name: COLUMN tenant_features.usage_limit; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.tenant_features.usage_limit IS 'Limite de uso (NULL = ilimitado).';


--
-- TOC entry 4459 (class 0 OID 0)
-- Dependencies: 257
-- Name: COLUMN tenant_features.current_usage; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.tenant_features.current_usage IS 'Uso atual da funcionalidade.';


--
-- TOC entry 4460 (class 0 OID 0)
-- Dependencies: 257
-- Name: COLUMN tenant_features.feature_config; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.tenant_features.feature_config IS 'Configurações específicas da funcionalidade em JSONB.';


--
-- TOC entry 4461 (class 0 OID 0)
-- Dependencies: 257
-- Name: COLUMN tenant_features.updated_by_user_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.tenant_features.updated_by_user_id IS 'ID da conta de acesso (usuário) que fez a última alteração.';


--
-- TOC entry 258 (class 1259 OID 86294)
-- Name: user_contexts; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.user_contexts (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    session_id character varying(40),
    context_type character varying(255) NOT NULL,
    context_id bigint,
    previous_context_type character varying(20),
    previous_context_id bigint,
    change_reason character varying(255),
    switched_at timestamp(0) without time zone DEFAULT now(),
    ip_address character varying(45),
    user_agent text,
    ended_at timestamp(0) without time zone,
    duration_seconds integer,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT user_contexts_change_reason_check CHECK (((change_reason)::text = ANY (ARRAY[('login'::character varying)::text, ('switch'::character varying)::text, ('impersonation_start'::character varying)::text, ('impersonation_end'::character varying)::text, ('forced_switch'::character varying)::text, ('session_timeout'::character varying)::text, ('logout'::character varying)::text, ('auto_switch'::character varying)::text]))),
    CONSTRAINT user_contexts_context_type_check CHECK (((context_type)::text = ANY (ARRAY[('system'::character varying)::text, ('company'::character varying)::text, ('establishment'::character varying)::text])))
);


ALTER TABLE master.user_contexts OWNER TO postgres;

--
-- TOC entry 4462 (class 0 OID 0)
-- Dependencies: 258
-- Name: TABLE user_contexts; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.user_contexts IS 'Histórico e controle de mudanças de contexto das contas de acesso.';


--
-- TOC entry 284 (class 1259 OID 87850)
-- Name: user_contexts_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.user_contexts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.user_contexts_id_seq OWNER TO postgres;

--
-- TOC entry 4463 (class 0 OID 0)
-- Dependencies: 284
-- Name: user_contexts_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.user_contexts_id_seq OWNED BY master.user_contexts.id;


--
-- TOC entry 283 (class 1259 OID 87807)
-- Name: user_establishments; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.user_establishments (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    establishment_id bigint NOT NULL,
    role_id bigint,
    is_primary boolean DEFAULT false,
    status character varying(20) DEFAULT 'active'::character varying,
    assigned_by_user_id bigint,
    assigned_at timestamp without time zone DEFAULT now(),
    expires_at timestamp without time zone,
    permissions jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone,
    deleted_at timestamp without time zone
);


ALTER TABLE master.user_establishments OWNER TO postgres;

--
-- TOC entry 4464 (class 0 OID 0)
-- Dependencies: 283
-- Name: TABLE user_establishments; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.user_establishments IS 'Relacionamento usuários com estabelecimentos - sistema multi-empresa';


--
-- TOC entry 4465 (class 0 OID 0)
-- Dependencies: 283
-- Name: COLUMN user_establishments.is_primary; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.user_establishments.is_primary IS 'Se este é o estabelecimento principal do usuário';


--
-- TOC entry 4466 (class 0 OID 0)
-- Dependencies: 283
-- Name: COLUMN user_establishments.status; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.user_establishments.status IS 'Status do relacionamento: active, inactive, suspended';


--
-- TOC entry 4467 (class 0 OID 0)
-- Dependencies: 283
-- Name: COLUMN user_establishments.permissions; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.user_establishments.permissions IS 'Permissões específicas do usuário neste estabelecimento';


--
-- TOC entry 282 (class 1259 OID 87806)
-- Name: user_establishments_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.user_establishments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.user_establishments_id_seq OWNER TO postgres;

--
-- TOC entry 4468 (class 0 OID 0)
-- Dependencies: 282
-- Name: user_establishments_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.user_establishments_id_seq OWNED BY master.user_establishments.id;


--
-- TOC entry 259 (class 1259 OID 86303)
-- Name: user_roles; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.user_roles (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    role_id bigint NOT NULL,
    context_type character varying(255) NOT NULL,
    context_id bigint NOT NULL,
    status character varying(255) DEFAULT 'active'::character varying NOT NULL,
    assigned_by_user_id bigint,
    assigned_at timestamp(0) without time zone DEFAULT now(),
    expires_at timestamp(0) without time zone,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone,
    CONSTRAINT user_roles_context_type_check CHECK (((context_type)::text = ANY (ARRAY[('system'::character varying)::text, ('company'::character varying)::text, ('establishment'::character varying)::text]))),
    CONSTRAINT user_roles_status_check CHECK (((status)::text = ANY (ARRAY[('active'::character varying)::text, ('inactive'::character varying)::text, ('suspended'::character varying)::text, ('expired'::character varying)::text])))
);


ALTER TABLE master.user_roles OWNER TO postgres;

--
-- TOC entry 4469 (class 0 OID 0)
-- Dependencies: 259
-- Name: TABLE user_roles; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.user_roles IS 'Relacionamento N:M entre contas de acesso (users) e papéis (roles) com contexto específico.';


--
-- TOC entry 4470 (class 0 OID 0)
-- Dependencies: 259
-- Name: COLUMN user_roles.user_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.user_roles.user_id IS 'ID da conta de acesso que recebe o papel.';


--
-- TOC entry 4471 (class 0 OID 0)
-- Dependencies: 259
-- Name: COLUMN user_roles.role_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.user_roles.role_id IS 'ID do papel atribuído.';


--
-- TOC entry 4472 (class 0 OID 0)
-- Dependencies: 259
-- Name: COLUMN user_roles.context_type; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.user_roles.context_type IS 'Tipo de contexto: system, company, establishment.';


--
-- TOC entry 4473 (class 0 OID 0)
-- Dependencies: 259
-- Name: COLUMN user_roles.context_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.user_roles.context_id IS 'ID da entidade de contexto (ex: company_id ou establishment_id).';


--
-- TOC entry 260 (class 1259 OID 86313)
-- Name: user_roles_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.user_roles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.user_roles_id_seq OWNER TO postgres;

--
-- TOC entry 4474 (class 0 OID 0)
-- Dependencies: 260
-- Name: user_roles_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.user_roles_id_seq OWNED BY master.user_roles.id;


--
-- TOC entry 261 (class 1259 OID 86314)
-- Name: users; Type: TABLE; Schema: master; Owner: postgres
--

CREATE TABLE master.users (
    id bigint NOT NULL,
    person_id bigint NOT NULL,
    email_address character varying(255) NOT NULL,
    email_verified_at timestamp(0) without time zone,
    password character varying(255) NOT NULL,
    remember_token character varying(100),
    is_active boolean DEFAULT true,
    is_system_admin boolean DEFAULT false,
    preferences jsonb,
    notification_settings jsonb,
    two_factor_secret text,
    two_factor_recovery_codes text,
    last_login_at timestamp(0) without time zone,
    password_changed_at timestamp(0) without time zone,
    created_at timestamp(0) without time zone DEFAULT now(),
    updated_at timestamp(0) without time zone,
    deleted_at timestamp(0) without time zone
);


ALTER TABLE master.users OWNER TO postgres;

--
-- TOC entry 4475 (class 0 OID 0)
-- Dependencies: 261
-- Name: TABLE users; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON TABLE master.users IS 'Tabela de Contas de Acesso. Armazena credenciais e configurações para login no sistema.';


--
-- TOC entry 4476 (class 0 OID 0)
-- Dependencies: 261
-- Name: COLUMN users.person_id; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.users.person_id IS 'Referência (FK) para o registro correspondente na tabela "people".';


--
-- TOC entry 4477 (class 0 OID 0)
-- Dependencies: 261
-- Name: COLUMN users.email_address; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.users.email_address IS 'Email único para login e comunicação, associado a esta conta.';


--
-- TOC entry 4478 (class 0 OID 0)
-- Dependencies: 261
-- Name: COLUMN users.is_system_admin; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.users.is_system_admin IS 'Flag para super administradores do sistema (privilégio da conta, não da pessoa).';


--
-- TOC entry 4479 (class 0 OID 0)
-- Dependencies: 261
-- Name: COLUMN users.preferences; Type: COMMENT; Schema: master; Owner: postgres
--

COMMENT ON COLUMN master.users.preferences IS 'Preferências de interface e uso do sistema para esta conta.';


--
-- TOC entry 262 (class 1259 OID 86322)
-- Name: users_id_seq; Type: SEQUENCE; Schema: master; Owner: postgres
--

CREATE SEQUENCE master.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE master.users_id_seq OWNER TO postgres;

--
-- TOC entry 4480 (class 0 OID 0)
-- Dependencies: 262
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: master; Owner: postgres
--

ALTER SEQUENCE master.users_id_seq OWNED BY master.users.id;


--
-- TOC entry 263 (class 1259 OID 86323)
-- Name: vw_addresses_with_geolocation; Type: VIEW; Schema: master; Owner: postgres
--

CREATE VIEW master.vw_addresses_with_geolocation AS
 SELECT id,
    addressable_type,
    addressable_id,
    type,
    concat_ws(', '::text, street, number, neighborhood, city, state, zip_code) AS full_address,
    latitude,
    longitude,
    quality_score,
    is_active,
    is_principal
   FROM master.addresses a
  WHERE ((latitude IS NOT NULL) AND (longitude IS NOT NULL));


ALTER VIEW master.vw_addresses_with_geolocation OWNER TO postgres;

--
-- TOC entry 264 (class 1259 OID 86328)
-- Name: vw_menu_hierarchy; Type: VIEW; Schema: master; Owner: postgres
--

CREATE VIEW master.vw_menu_hierarchy AS
 WITH RECURSIVE menu_tree AS (
         SELECT m.id,
            m.parent_id,
            m.name,
            m.slug,
            m.path,
            m.level,
            m.sort_order,
            m.url,
            m.route_name,
            m.route_params,
            m.icon,
            m.permission_name,
            m.required_permissions,
            m.required_roles,
            m.type,
            m.is_active,
            m.is_visible,
            m.visible_in_menu,
            m.badge_text,
            m.badge_color,
            m.company_specific,
            m.establishment_specific,
            (m.name)::text AS full_path_name,
            ARRAY[m.id] AS id_path
           FROM master.menus m
          WHERE ((m.parent_id IS NULL) AND (m.is_active = true) AND (m.deleted_at IS NULL))
        UNION ALL
         SELECT m.id,
            m.parent_id,
            m.name,
            m.slug,
            m.path,
            m.level,
            m.sort_order,
            m.url,
            m.route_name,
            m.route_params,
            m.icon,
            m.permission_name,
            m.required_permissions,
            m.required_roles,
            m.type,
            m.is_active,
            m.is_visible,
            m.visible_in_menu,
            m.badge_text,
            m.badge_color,
            m.company_specific,
            m.establishment_specific,
            ((mt.full_path_name || ' → '::text) || (m.name)::text),
            (mt.id_path || m.id)
           FROM (master.menus m
             JOIN menu_tree mt ON ((m.parent_id = mt.id)))
          WHERE ((m.is_active = true) AND (m.deleted_at IS NULL))
        )
 SELECT id,
    parent_id,
    name,
    slug,
    path,
    level,
    sort_order,
    url,
    route_name,
    route_params,
    icon,
    permission_name,
    required_permissions,
    required_roles,
    type,
    is_active,
    is_visible,
    visible_in_menu,
    badge_text,
    badge_color,
    company_specific,
    establishment_specific,
    full_path_name,
    id_path
   FROM menu_tree
  ORDER BY level, sort_order;


ALTER VIEW master.vw_menu_hierarchy OWNER TO postgres;

--
-- TOC entry 265 (class 1259 OID 86333)
-- Name: vw_menus_by_level; Type: VIEW; Schema: master; Owner: postgres
--

CREATE VIEW master.vw_menus_by_level AS
 SELECT level,
    count(*) AS menu_count,
    string_agg((name)::text, ', '::text ORDER BY sort_order) AS menu_names
   FROM master.menus
  WHERE ((is_active = true) AND (deleted_at IS NULL))
  GROUP BY level
  ORDER BY level;


ALTER VIEW master.vw_menus_by_level OWNER TO postgres;

--
-- TOC entry 266 (class 1259 OID 86338)
-- Name: vw_permissions_by_module; Type: VIEW; Schema: master; Owner: postgres
--

CREATE VIEW master.vw_permissions_by_module AS
 SELECT module,
    count(*) AS total_permissions,
    count(
        CASE
            WHEN ((context_level)::text = 'system'::text) THEN 1
            ELSE NULL::integer
        END) AS system_permissions,
    count(
        CASE
            WHEN ((context_level)::text = 'company'::text) THEN 1
            ELSE NULL::integer
        END) AS company_permissions,
    count(
        CASE
            WHEN ((context_level)::text = 'establishment'::text) THEN 1
            ELSE NULL::integer
        END) AS establishment_permissions,
    array_agg(DISTINCT action ORDER BY action) AS available_actions,
    array_agg(DISTINCT resource ORDER BY resource) AS available_resources
   FROM master.permissions p
  WHERE (is_active = true)
  GROUP BY module
  ORDER BY module;


ALTER VIEW master.vw_permissions_by_module OWNER TO postgres;

--
-- TOC entry 267 (class 1259 OID 86343)
-- Name: vw_permissions_hierarchy; Type: VIEW; Schema: master; Owner: postgres
--

CREATE VIEW master.vw_permissions_hierarchy AS
 SELECT id,
    name,
    display_name,
    module,
    action,
    resource,
    context_level,
        CASE context_level
            WHEN 'system'::text THEN 'Sistema'::text
            WHEN 'company'::text THEN 'Empresa'::text
            WHEN 'establishment'::text THEN 'Estabelecimento'::text
            ELSE NULL::text
        END AS context_display,
        CASE action
            WHEN 'view'::text THEN 1
            WHEN 'create'::text THEN 2
            WHEN 'update'::text THEN 3
            WHEN 'delete'::text THEN 4
            WHEN 'manage'::text THEN 5
            ELSE 6
        END AS action_weight,
    is_active
   FROM master.permissions p
  ORDER BY module,
        CASE action
            WHEN 'view'::text THEN 1
            WHEN 'create'::text THEN 2
            WHEN 'update'::text THEN 3
            WHEN 'delete'::text THEN 4
            WHEN 'manage'::text THEN 5
            ELSE 6
        END, resource;


ALTER VIEW master.vw_permissions_hierarchy OWNER TO postgres;

--
-- TOC entry 268 (class 1259 OID 86348)
-- Name: vw_recent_privacy_operations; Type: VIEW; Schema: master; Owner: postgres
--

CREATE VIEW master.vw_recent_privacy_operations AS
 SELECT dpl.id,
    dpl.operation_type,
    dpl.data_category,
    p.name AS subject_name,
    u.email_address AS operator_email,
    dpl.purpose,
    dpl.legal_basis,
    dpl.is_sensitive_data,
    dpl.created_at
   FROM ((master.data_privacy_logs dpl
     JOIN master.people p ON ((dpl.person_id = p.id)))
     LEFT JOIN master.users u ON ((dpl.operator_id = u.id)))
  WHERE (dpl.created_at >= (now() - '7 days'::interval))
  ORDER BY dpl.created_at DESC;


ALTER VIEW master.vw_recent_privacy_operations OWNER TO postgres;

--
-- TOC entry 269 (class 1259 OID 86353)
-- Name: vw_role_permission_stats; Type: VIEW; Schema: master; Owner: postgres
--

CREATE VIEW master.vw_role_permission_stats AS
 SELECT r.id AS role_id,
    r.name AS role_name,
    r.display_name AS role_display_name,
    r.level AS role_level,
    count(rp.permission_id) AS total_permissions,
    count(
        CASE
            WHEN ((p.context_level)::text = 'system'::text) THEN 1
            ELSE NULL::integer
        END) AS system_permissions,
    count(
        CASE
            WHEN ((p.context_level)::text = 'company'::text) THEN 1
            ELSE NULL::integer
        END) AS company_permissions,
    count(
        CASE
            WHEN ((p.context_level)::text = 'establishment'::text) THEN 1
            ELSE NULL::integer
        END) AS establishment_permissions,
    count(
        CASE
            WHEN ((p.action)::text = 'view'::text) THEN 1
            ELSE NULL::integer
        END) AS view_permissions,
    count(
        CASE
            WHEN ((p.action)::text = 'create'::text) THEN 1
            ELSE NULL::integer
        END) AS create_permissions,
    count(
        CASE
            WHEN ((p.action)::text = 'update'::text) THEN 1
            ELSE NULL::integer
        END) AS update_permissions,
    count(
        CASE
            WHEN ((p.action)::text = 'delete'::text) THEN 1
            ELSE NULL::integer
        END) AS delete_permissions,
    count(
        CASE
            WHEN ((p.action)::text = 'manage'::text) THEN 1
            ELSE NULL::integer
        END) AS manage_permissions
   FROM ((master.roles r
     LEFT JOIN master.role_permissions rp ON ((r.id = rp.role_id)))
     LEFT JOIN master.permissions p ON (((rp.permission_id = p.id) AND (p.is_active = true))))
  WHERE (r.is_active = true)
  GROUP BY r.id, r.name, r.display_name, r.level
  ORDER BY r.level DESC, r.name;


ALTER VIEW master.vw_role_permission_stats OWNER TO postgres;

--
-- TOC entry 270 (class 1259 OID 86358)
-- Name: vw_role_permissions; Type: VIEW; Schema: master; Owner: postgres
--

CREATE VIEW master.vw_role_permissions AS
 SELECT r.id AS role_id,
    r.name AS role_name,
    r.display_name AS role_display_name,
    r.level AS role_level,
    r.context_type AS role_context,
    p.id AS permission_id,
    p.name AS permission_name,
    p.display_name AS permission_display_name,
    p.module AS permission_module,
    p.action AS permission_action,
    p.resource AS permission_resource,
    p.context_level AS permission_context,
    rp.granted_at,
    pe.name AS granted_by_name
   FROM ((((master.role_permissions rp
     JOIN master.roles r ON ((rp.role_id = r.id)))
     JOIN master.permissions p ON ((rp.permission_id = p.id)))
     LEFT JOIN master.users u ON ((rp.granted_by_user_id = u.id)))
     LEFT JOIN master.people pe ON ((u.person_id = pe.id)))
  WHERE ((r.is_active = true) AND (p.is_active = true))
  ORDER BY r.level DESC, r.name, p.module, p.action, p.resource;


ALTER VIEW master.vw_role_permissions OWNER TO postgres;

--
-- TOC entry 271 (class 1259 OID 86363)
-- Name: vw_roles_hierarchy; Type: VIEW; Schema: master; Owner: postgres
--

CREATE VIEW master.vw_roles_hierarchy AS
 SELECT id,
    name,
    display_name,
    level,
    context_type,
    ( SELECT count(*) AS count
           FROM master.roles sr
          WHERE ((sr.level < r.level) AND ((sr.context_type)::text = (r.context_type)::text) AND (sr.is_active = true))) AS subordinate_roles_count,
    ( SELECT count(*) AS count
           FROM master.roles sr
          WHERE ((sr.level > r.level) AND ((sr.context_type)::text = (r.context_type)::text) AND (sr.is_active = true))) AS superior_roles_count
   FROM master.roles r
  WHERE (is_active = true)
  ORDER BY context_type, level DESC;


ALTER VIEW master.vw_roles_hierarchy OWNER TO postgres;

--
-- TOC entry 272 (class 1259 OID 86368)
-- Name: vw_roles_with_context; Type: VIEW; Schema: master; Owner: postgres
--

CREATE VIEW master.vw_roles_with_context AS
 SELECT id,
    name,
    display_name,
    description,
    level,
    context_type,
        CASE context_type
            WHEN 'system'::text THEN 'Sistema'::text
            WHEN 'company'::text THEN 'Empresa'::text
            WHEN 'establishment'::text THEN 'Estabelecimento'::text
            ELSE NULL::text
        END AS context_type_display,
    is_active,
    is_system_role,
    created_at,
        CASE
            WHEN (level >= 90) THEN 'Administrador'::text
            WHEN (level >= 70) THEN 'Gerencial'::text
            WHEN (level >= 50) THEN 'Operacional'::text
            WHEN (level >= 30) THEN 'Apoio'::text
            ELSE 'Visualização'::text
        END AS classification
   FROM master.roles r
  ORDER BY level DESC, name;


ALTER VIEW master.vw_roles_with_context OWNER TO postgres;

--
-- TOC entry 273 (class 1259 OID 86373)
-- Name: vw_whatsapp_numbers; Type: VIEW; Schema: master; Owner: postgres
--

CREATE VIEW master.vw_whatsapp_numbers AS
 SELECT id,
    phoneable_type,
    phoneable_id,
    phone_name,
    whatsapp_formatted,
    whatsapp_business,
    whatsapp_name,
    accepts_whatsapp_marketing,
    accepts_whatsapp_notifications,
    whatsapp_preferred_time_start,
    whatsapp_preferred_time_end,
    contact_priority,
    verified_at,
    is_active
   FROM master.phones p
  WHERE ((is_whatsapp = true) AND (is_active = true) AND (whatsapp_formatted IS NOT NULL))
  ORDER BY contact_priority;


ALTER VIEW master.vw_whatsapp_numbers OWNER TO postgres;

--
-- TOC entry 287 (class 1259 OID 94130)
-- Name: migrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.migrations (
    id integer NOT NULL,
    migration character varying(255) NOT NULL,
    batch integer NOT NULL
);


ALTER TABLE public.migrations OWNER TO postgres;

--
-- TOC entry 286 (class 1259 OID 94129)
-- Name: migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.migrations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.migrations_id_seq OWNER TO postgres;

--
-- TOC entry 4481 (class 0 OID 0)
-- Dependencies: 286
-- Name: migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.migrations_id_seq OWNED BY public.migrations.id;


--
-- TOC entry 285 (class 1259 OID 94120)
-- Name: sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sessions (
    id character varying(255) NOT NULL,
    user_id bigint,
    ip_address character varying(45),
    user_agent text,
    payload text NOT NULL,
    last_activity integer NOT NULL
);


ALTER TABLE public.sessions OWNER TO postgres;

--
-- TOC entry 3541 (class 2604 OID 87785)
-- Name: addresses id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.addresses ALTER COLUMN id SET DEFAULT nextval('master.addresses_id_seq'::regclass);


--
-- TOC entry 3549 (class 2604 OID 87787)
-- Name: clients id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.clients ALTER COLUMN id SET DEFAULT nextval('master.clients_id_seq'::regclass);


--
-- TOC entry 3552 (class 2604 OID 87789)
-- Name: companies id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.companies ALTER COLUMN id SET DEFAULT nextval('master.companies_id_seq'::regclass);


--
-- TOC entry 3561 (class 2604 OID 86831)
-- Name: data_privacy_logs id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.data_privacy_logs ALTER COLUMN id SET DEFAULT nextval('master.data_privacy_logs_id_seq'::regclass);


--
-- TOC entry 3564 (class 2604 OID 87793)
-- Name: documents id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.documents ALTER COLUMN id SET DEFAULT nextval('master.documents_id_seq'::regclass);


--
-- TOC entry 3569 (class 2604 OID 87783)
-- Name: emails id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.emails ALTER COLUMN id SET DEFAULT nextval('master.emails_id_seq'::regclass);


--
-- TOC entry 3579 (class 2604 OID 87791)
-- Name: establishments id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.establishments ALTER COLUMN id SET DEFAULT nextval('master.establishments_id_seq'::regclass);


--
-- TOC entry 3584 (class 2604 OID 86832)
-- Name: failed_jobs id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.failed_jobs ALTER COLUMN id SET DEFAULT nextval('master.failed_jobs_id_seq'::regclass);


--
-- TOC entry 3586 (class 2604 OID 86833)
-- Name: jobs id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.jobs ALTER COLUMN id SET DEFAULT nextval('master.jobs_id_seq'::regclass);


--
-- TOC entry 3587 (class 2604 OID 86834)
-- Name: lgpd_audit_config id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.lgpd_audit_config ALTER COLUMN id SET DEFAULT nextval('master.lgpd_audit_config_id_seq'::regclass);


--
-- TOC entry 3592 (class 2604 OID 86835)
-- Name: lgpd_incidents id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.lgpd_incidents ALTER COLUMN id SET DEFAULT nextval('master.lgpd_incidents_id_seq'::regclass);


--
-- TOC entry 3613 (class 2604 OID 86836)
-- Name: migrations id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.migrations ALTER COLUMN id SET DEFAULT nextval('master.migrations_id_seq'::regclass);


--
-- TOC entry 3614 (class 2604 OID 86837)
-- Name: people id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.people ALTER COLUMN id SET DEFAULT nextval('master.people_id_seq'::regclass);


--
-- TOC entry 3618 (class 2604 OID 86838)
-- Name: permissions id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.permissions ALTER COLUMN id SET DEFAULT nextval('master.permissions_id_seq'::regclass);


--
-- TOC entry 3640 (class 2604 OID 87795)
-- Name: professionals id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.professionals ALTER COLUMN id SET DEFAULT nextval('master.professionals_id_seq'::regclass);


--
-- TOC entry 3643 (class 2604 OID 86839)
-- Name: query_audit_logs id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.query_audit_logs ALTER COLUMN id SET DEFAULT nextval('master.query_audit_logs_id_seq'::regclass);


--
-- TOC entry 3646 (class 2604 OID 86840)
-- Name: role_permissions id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.role_permissions ALTER COLUMN id SET DEFAULT nextval('master.role_permissions_id_seq'::regclass);


--
-- TOC entry 3648 (class 2604 OID 86841)
-- Name: roles id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.roles ALTER COLUMN id SET DEFAULT nextval('master.roles_id_seq'::regclass);


--
-- TOC entry 3659 (class 2604 OID 87851)
-- Name: user_contexts id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_contexts ALTER COLUMN id SET DEFAULT nextval('master.user_contexts_id_seq'::regclass);


--
-- TOC entry 3671 (class 2604 OID 87810)
-- Name: user_establishments id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_establishments ALTER COLUMN id SET DEFAULT nextval('master.user_establishments_id_seq'::regclass);


--
-- TOC entry 3663 (class 2604 OID 86842)
-- Name: user_roles id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_roles ALTER COLUMN id SET DEFAULT nextval('master.user_roles_id_seq'::regclass);


--
-- TOC entry 3667 (class 2604 OID 86843)
-- Name: users id; Type: DEFAULT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.users ALTER COLUMN id SET DEFAULT nextval('master.users_id_seq'::regclass);


--
-- TOC entry 3677 (class 2604 OID 94133)
-- Name: migrations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.migrations ALTER COLUMN id SET DEFAULT nextval('public.migrations_id_seq'::regclass);


--
-- TOC entry 3727 (class 2606 OID 86392)
-- Name: activity_logs_2025_08 activity_logs_2025_08_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.activity_logs_2025_08
    ADD CONSTRAINT activity_logs_2025_08_pkey PRIMARY KEY (id, created_at);


--
-- TOC entry 3716 (class 2606 OID 86394)
-- Name: activity_logs activity_logs_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.activity_logs
    ADD CONSTRAINT activity_logs_pkey PRIMARY KEY (id, created_at);


--
-- TOC entry 3730 (class 2606 OID 86396)
-- Name: addresses addresses_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.addresses
    ADD CONSTRAINT addresses_pkey PRIMARY KEY (id);


--
-- TOC entry 3998 (class 2606 OID 94192)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 3750 (class 2606 OID 86398)
-- Name: cache_locks cache_locks_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.cache_locks
    ADD CONSTRAINT cache_locks_pkey PRIMARY KEY (key);


--
-- TOC entry 3748 (class 2606 OID 86400)
-- Name: cache cache_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.cache
    ADD CONSTRAINT cache_pkey PRIMARY KEY (key);


--
-- TOC entry 3753 (class 2606 OID 86402)
-- Name: clients clients_establishment_id_client_code_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.clients
    ADD CONSTRAINT clients_establishment_id_client_code_unique UNIQUE (establishment_id, client_code);


--
-- TOC entry 3756 (class 2606 OID 86404)
-- Name: clients clients_establishment_id_person_id_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.clients
    ADD CONSTRAINT clients_establishment_id_person_id_unique UNIQUE (establishment_id, person_id);


--
-- TOC entry 3759 (class 2606 OID 86406)
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- TOC entry 3765 (class 2606 OID 86408)
-- Name: companies companies_person_id_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.companies
    ADD CONSTRAINT companies_person_id_unique UNIQUE (person_id);


--
-- TOC entry 3767 (class 2606 OID 86410)
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- TOC entry 3771 (class 2606 OID 86412)
-- Name: company_settings company_settings_company_id_setting_key_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.company_settings
    ADD CONSTRAINT company_settings_company_id_setting_key_unique UNIQUE (company_id, setting_key);


--
-- TOC entry 3773 (class 2606 OID 86414)
-- Name: company_settings company_settings_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.company_settings
    ADD CONSTRAINT company_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 3782 (class 2606 OID 86416)
-- Name: consent_records consent_records_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.consent_records
    ADD CONSTRAINT consent_records_pkey PRIMARY KEY (id);


--
-- TOC entry 3792 (class 2606 OID 86418)
-- Name: data_privacy_logs data_privacy_logs_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.data_privacy_logs
    ADD CONSTRAINT data_privacy_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 3798 (class 2606 OID 86420)
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- TOC entry 3805 (class 2606 OID 86422)
-- Name: emails emails_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.emails
    ADD CONSTRAINT emails_pkey PRIMARY KEY (id);


--
-- TOC entry 3808 (class 2606 OID 86424)
-- Name: establishment_settings establishment_settings_establishment_id_setting_key_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.establishment_settings
    ADD CONSTRAINT establishment_settings_establishment_id_setting_key_unique UNIQUE (establishment_id, setting_key);


--
-- TOC entry 3810 (class 2606 OID 86426)
-- Name: establishment_settings establishment_settings_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.establishment_settings
    ADD CONSTRAINT establishment_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 3815 (class 2606 OID 86428)
-- Name: establishments establishments_company_id_code_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.establishments
    ADD CONSTRAINT establishments_company_id_code_unique UNIQUE (company_id, code);


--
-- TOC entry 3821 (class 2606 OID 86430)
-- Name: establishments establishments_person_id_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.establishments
    ADD CONSTRAINT establishments_person_id_unique UNIQUE (person_id);


--
-- TOC entry 3823 (class 2606 OID 86432)
-- Name: establishments establishments_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.establishments
    ADD CONSTRAINT establishments_pkey PRIMARY KEY (id);


--
-- TOC entry 3825 (class 2606 OID 86434)
-- Name: failed_jobs failed_jobs_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.failed_jobs
    ADD CONSTRAINT failed_jobs_pkey PRIMARY KEY (id);


--
-- TOC entry 3829 (class 2606 OID 86436)
-- Name: job_batches job_batches_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.job_batches
    ADD CONSTRAINT job_batches_pkey PRIMARY KEY (id);


--
-- TOC entry 3831 (class 2606 OID 86438)
-- Name: jobs jobs_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);


--
-- TOC entry 3834 (class 2606 OID 86440)
-- Name: lgpd_audit_config lgpd_audit_config_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.lgpd_audit_config
    ADD CONSTRAINT lgpd_audit_config_pkey PRIMARY KEY (id);


--
-- TOC entry 3842 (class 2606 OID 86442)
-- Name: lgpd_incidents lgpd_incidents_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.lgpd_incidents
    ADD CONSTRAINT lgpd_incidents_pkey PRIMARY KEY (id);


--
-- TOC entry 3827 (class 2606 OID 86444)
-- Name: failed_jobs master_failed_jobs_uuid_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.failed_jobs
    ADD CONSTRAINT master_failed_jobs_uuid_unique UNIQUE (uuid);


--
-- TOC entry 3844 (class 2606 OID 86446)
-- Name: lgpd_incidents master_lgpd_incidents_incident_id_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.lgpd_incidents
    ADD CONSTRAINT master_lgpd_incidents_incident_id_unique UNIQUE (incident_id);


--
-- TOC entry 3857 (class 2606 OID 86448)
-- Name: menus menus_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.menus
    ADD CONSTRAINT menus_pkey PRIMARY KEY (id);


--
-- TOC entry 3862 (class 2606 OID 86450)
-- Name: menus menus_slug_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.menus
    ADD CONSTRAINT menus_slug_unique UNIQUE (slug);


--
-- TOC entry 3866 (class 2606 OID 86452)
-- Name: migrations migrations_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.migrations
    ADD CONSTRAINT migrations_pkey PRIMARY KEY (id);


--
-- TOC entry 3868 (class 2606 OID 86454)
-- Name: password_reset_tokens password_reset_tokens_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (email);


--
-- TOC entry 3874 (class 2606 OID 86456)
-- Name: people people_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.people
    ADD CONSTRAINT people_pkey PRIMARY KEY (id);


--
-- TOC entry 3877 (class 2606 OID 86458)
-- Name: people people_tax_id_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.people
    ADD CONSTRAINT people_tax_id_unique UNIQUE (tax_id);


--
-- TOC entry 3882 (class 2606 OID 86460)
-- Name: permissions permissions_module_action_resource_context_level_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.permissions
    ADD CONSTRAINT permissions_module_action_resource_context_level_unique UNIQUE (module, action, resource, context_level);


--
-- TOC entry 3886 (class 2606 OID 86462)
-- Name: permissions permissions_name_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.permissions
    ADD CONSTRAINT permissions_name_unique UNIQUE (name);


--
-- TOC entry 3888 (class 2606 OID 86464)
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 3898 (class 2606 OID 86466)
-- Name: phones phones_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.phones
    ADD CONSTRAINT phones_pkey PRIMARY KEY (id);


--
-- TOC entry 3906 (class 2606 OID 86468)
-- Name: professionals professionals_establishment_id_professional_code_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.professionals
    ADD CONSTRAINT professionals_establishment_id_professional_code_unique UNIQUE (establishment_id, professional_code);


--
-- TOC entry 3909 (class 2606 OID 86470)
-- Name: professionals professionals_pf_person_id_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.professionals
    ADD CONSTRAINT professionals_pf_person_id_unique UNIQUE (pf_person_id);


--
-- TOC entry 3912 (class 2606 OID 86472)
-- Name: professionals professionals_pj_person_id_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.professionals
    ADD CONSTRAINT professionals_pj_person_id_unique UNIQUE (pj_person_id);


--
-- TOC entry 3914 (class 2606 OID 86474)
-- Name: professionals professionals_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.professionals
    ADD CONSTRAINT professionals_pkey PRIMARY KEY (id);


--
-- TOC entry 3925 (class 2606 OID 86476)
-- Name: query_audit_logs query_audit_logs_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.query_audit_logs
    ADD CONSTRAINT query_audit_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 3930 (class 2606 OID 86478)
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 3933 (class 2606 OID 86480)
-- Name: role_permissions role_permissions_role_id_permission_id_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.role_permissions
    ADD CONSTRAINT role_permissions_role_id_permission_id_unique UNIQUE (role_id, permission_id);


--
-- TOC entry 3940 (class 2606 OID 86482)
-- Name: roles roles_name_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.roles
    ADD CONSTRAINT roles_name_unique UNIQUE (name);


--
-- TOC entry 3942 (class 2606 OID 86484)
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- TOC entry 3946 (class 2606 OID 86486)
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- TOC entry 3952 (class 2606 OID 86488)
-- Name: tenant_features tenant_features_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.tenant_features
    ADD CONSTRAINT tenant_features_pkey PRIMARY KEY (id);


--
-- TOC entry 3954 (class 2606 OID 86490)
-- Name: tenant_features tenant_features_tenant_type_tenant_id_feature_key_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.tenant_features
    ADD CONSTRAINT tenant_features_tenant_type_tenant_id_feature_key_unique UNIQUE (tenant_type, tenant_id, feature_key);


--
-- TOC entry 3837 (class 2606 OID 86492)
-- Name: lgpd_audit_config uk_audit_config; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.lgpd_audit_config
    ADD CONSTRAINT uk_audit_config UNIQUE (table_name, operation);


--
-- TOC entry 3959 (class 2606 OID 86494)
-- Name: user_contexts user_contexts_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_contexts
    ADD CONSTRAINT user_contexts_pkey PRIMARY KEY (id);


--
-- TOC entry 3988 (class 2606 OID 87819)
-- Name: user_establishments user_establishments_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_establishments
    ADD CONSTRAINT user_establishments_pkey PRIMARY KEY (id);


--
-- TOC entry 3990 (class 2606 OID 87821)
-- Name: user_establishments user_establishments_user_id_establishment_id_key; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_establishments
    ADD CONSTRAINT user_establishments_user_id_establishment_id_key UNIQUE (user_id, establishment_id);


--
-- TOC entry 3967 (class 2606 OID 86496)
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);


--
-- TOC entry 3972 (class 2606 OID 86498)
-- Name: user_roles user_roles_user_id_role_id_context_type_context_id_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_roles
    ADD CONSTRAINT user_roles_user_id_role_id_context_type_context_id_unique UNIQUE (user_id, role_id, context_type, context_id);


--
-- TOC entry 3975 (class 2606 OID 86500)
-- Name: users users_email_address_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.users
    ADD CONSTRAINT users_email_address_unique UNIQUE (email_address);


--
-- TOC entry 3979 (class 2606 OID 86502)
-- Name: users users_person_id_unique; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.users
    ADD CONSTRAINT users_person_id_unique UNIQUE (person_id);


--
-- TOC entry 3981 (class 2606 OID 86504)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 3996 (class 2606 OID 94135)
-- Name: migrations migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.migrations
    ADD CONSTRAINT migrations_pkey PRIMARY KEY (id);


--
-- TOC entry 3993 (class 2606 OID 94126)
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- TOC entry 3723 (class 1259 OID 86505)
-- Name: activity_logs_2025_08_causer_type_causer_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX activity_logs_2025_08_causer_type_causer_id_index ON master.activity_logs_2025_08 USING btree (causer_type, causer_id);


--
-- TOC entry 3724 (class 1259 OID 86506)
-- Name: activity_logs_2025_08_created_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX activity_logs_2025_08_created_at_index ON master.activity_logs_2025_08 USING btree (created_at);


--
-- TOC entry 3725 (class 1259 OID 86507)
-- Name: activity_logs_2025_08_log_name_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX activity_logs_2025_08_log_name_index ON master.activity_logs_2025_08 USING btree (log_name);


--
-- TOC entry 3728 (class 1259 OID 86508)
-- Name: activity_logs_2025_08_subject_type_subject_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX activity_logs_2025_08_subject_type_subject_id_index ON master.activity_logs_2025_08 USING btree (subject_type, subject_id);


--
-- TOC entry 3712 (class 1259 OID 86509)
-- Name: activity_logs_causer_type_causer_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX activity_logs_causer_type_causer_id_index ON master.activity_logs USING btree (causer_type, causer_id);


--
-- TOC entry 3713 (class 1259 OID 86510)
-- Name: activity_logs_created_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX activity_logs_created_at_index ON master.activity_logs USING btree (created_at);


--
-- TOC entry 3714 (class 1259 OID 86511)
-- Name: activity_logs_log_name_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX activity_logs_log_name_index ON master.activity_logs USING btree (log_name);


--
-- TOC entry 3717 (class 1259 OID 86512)
-- Name: activity_logs_subject_type_subject_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX activity_logs_subject_type_subject_id_index ON master.activity_logs USING btree (subject_type, subject_id);


--
-- TOC entry 3751 (class 1259 OID 86513)
-- Name: clients_deleted_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX clients_deleted_at_index ON master.clients USING btree (deleted_at);


--
-- TOC entry 3754 (class 1259 OID 86514)
-- Name: clients_establishment_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX clients_establishment_id_index ON master.clients USING btree (establishment_id);


--
-- TOC entry 3757 (class 1259 OID 86515)
-- Name: clients_person_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX clients_person_id_index ON master.clients USING btree (person_id);


--
-- TOC entry 3760 (class 1259 OID 86516)
-- Name: clients_status_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX clients_status_index ON master.clients USING btree (status);


--
-- TOC entry 3761 (class 1259 OID 86517)
-- Name: companies_deleted_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX companies_deleted_at_index ON master.companies USING btree (deleted_at);


--
-- TOC entry 3762 (class 1259 OID 86518)
-- Name: companies_metadata_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX companies_metadata_fulltext ON master.companies USING gin (to_tsvector('english'::regconfig, metadata));


--
-- TOC entry 3763 (class 1259 OID 86519)
-- Name: companies_person_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX companies_person_id_index ON master.companies USING btree (person_id);


--
-- TOC entry 3768 (class 1259 OID 86520)
-- Name: companies_settings_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX companies_settings_fulltext ON master.companies USING gin (to_tsvector('english'::regconfig, settings));


--
-- TOC entry 3769 (class 1259 OID 86521)
-- Name: company_settings_company_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX company_settings_company_id_index ON master.company_settings USING btree (company_id);


--
-- TOC entry 3774 (class 1259 OID 86522)
-- Name: company_settings_setting_category_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX company_settings_setting_category_index ON master.company_settings USING btree (setting_category);


--
-- TOC entry 3775 (class 1259 OID 86523)
-- Name: company_settings_setting_key_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX company_settings_setting_key_index ON master.company_settings USING btree (setting_key);


--
-- TOC entry 3776 (class 1259 OID 86524)
-- Name: company_settings_setting_value_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX company_settings_setting_value_fulltext ON master.company_settings USING gin (to_tsvector('english'::regconfig, setting_value));


--
-- TOC entry 3777 (class 1259 OID 86525)
-- Name: company_settings_updated_by_user_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX company_settings_updated_by_user_id_index ON master.company_settings USING btree (updated_by_user_id);


--
-- TOC entry 3778 (class 1259 OID 86526)
-- Name: consent_records_consent_type_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX consent_records_consent_type_index ON master.consent_records USING btree (consent_type);


--
-- TOC entry 3779 (class 1259 OID 86527)
-- Name: consent_records_person_id_consent_type_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX consent_records_person_id_consent_type_index ON master.consent_records USING btree (person_id, consent_type);


--
-- TOC entry 3780 (class 1259 OID 86528)
-- Name: consent_records_person_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX consent_records_person_id_index ON master.consent_records USING btree (person_id);


--
-- TOC entry 3783 (class 1259 OID 86529)
-- Name: consent_records_status_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX consent_records_status_index ON master.consent_records USING btree (status);


--
-- TOC entry 3786 (class 1259 OID 86530)
-- Name: data_privacy_logs_created_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX data_privacy_logs_created_at_index ON master.data_privacy_logs USING btree (created_at);


--
-- TOC entry 3787 (class 1259 OID 86531)
-- Name: data_privacy_logs_is_sensitive_data_created_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX data_privacy_logs_is_sensitive_data_created_at_index ON master.data_privacy_logs USING btree (is_sensitive_data, created_at);


--
-- TOC entry 3788 (class 1259 OID 86532)
-- Name: data_privacy_logs_operation_type_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX data_privacy_logs_operation_type_index ON master.data_privacy_logs USING btree (operation_type);


--
-- TOC entry 3789 (class 1259 OID 86533)
-- Name: data_privacy_logs_operator_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX data_privacy_logs_operator_id_index ON master.data_privacy_logs USING btree (operator_id);


--
-- TOC entry 3790 (class 1259 OID 86534)
-- Name: data_privacy_logs_person_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX data_privacy_logs_person_id_index ON master.data_privacy_logs USING btree (person_id);


--
-- TOC entry 3793 (class 1259 OID 86535)
-- Name: documents_deleted_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX documents_deleted_at_index ON master.documents USING btree (deleted_at);


--
-- TOC entry 3794 (class 1259 OID 86536)
-- Name: documents_documentable_type_documentable_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX documents_documentable_type_documentable_id_index ON master.documents USING btree (documentable_type, documentable_id);


--
-- TOC entry 3795 (class 1259 OID 86537)
-- Name: documents_expires_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX documents_expires_at_index ON master.documents USING btree (expires_at);


--
-- TOC entry 3796 (class 1259 OID 86538)
-- Name: documents_file_hash_sha256_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX documents_file_hash_sha256_index ON master.documents USING btree (file_hash_sha256);


--
-- TOC entry 3799 (class 1259 OID 86539)
-- Name: documents_tags_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX documents_tags_fulltext ON master.documents USING gin (to_tsvector('english'::regconfig, tags));


--
-- TOC entry 3800 (class 1259 OID 86540)
-- Name: documents_type_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX documents_type_index ON master.documents USING btree (type);


--
-- TOC entry 3801 (class 1259 OID 86541)
-- Name: emails_deleted_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX emails_deleted_at_index ON master.emails USING btree (deleted_at);


--
-- TOC entry 3802 (class 1259 OID 86542)
-- Name: emails_email_address_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX emails_email_address_index ON master.emails USING btree (email_address);


--
-- TOC entry 3803 (class 1259 OID 86543)
-- Name: emails_emailable_type_emailable_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX emails_emailable_type_emailable_id_index ON master.emails USING btree (emailable_type, emailable_id);


--
-- TOC entry 3806 (class 1259 OID 86544)
-- Name: establishment_settings_establishment_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX establishment_settings_establishment_id_index ON master.establishment_settings USING btree (establishment_id);


--
-- TOC entry 3811 (class 1259 OID 86545)
-- Name: establishment_settings_setting_category_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX establishment_settings_setting_category_index ON master.establishment_settings USING btree (setting_category);


--
-- TOC entry 3812 (class 1259 OID 86546)
-- Name: establishment_settings_setting_key_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX establishment_settings_setting_key_index ON master.establishment_settings USING btree (setting_key);


--
-- TOC entry 3813 (class 1259 OID 86547)
-- Name: establishment_settings_setting_value_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX establishment_settings_setting_value_fulltext ON master.establishment_settings USING gin (to_tsvector('english'::regconfig, setting_value));


--
-- TOC entry 3816 (class 1259 OID 86548)
-- Name: establishments_company_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX establishments_company_id_index ON master.establishments USING btree (company_id);


--
-- TOC entry 3817 (class 1259 OID 86549)
-- Name: establishments_company_id_is_principal_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX establishments_company_id_is_principal_index ON master.establishments USING btree (company_id, is_principal);


--
-- TOC entry 3818 (class 1259 OID 86550)
-- Name: establishments_deleted_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX establishments_deleted_at_index ON master.establishments USING btree (deleted_at);


--
-- TOC entry 3819 (class 1259 OID 86551)
-- Name: establishments_person_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX establishments_person_id_index ON master.establishments USING btree (person_id);


--
-- TOC entry 3718 (class 1259 OID 86552)
-- Name: idx_activity_logs_audit; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_activity_logs_audit ON master.activity_logs USING btree (created_at, ip_address);


--
-- TOC entry 3719 (class 1259 OID 86553)
-- Name: idx_activity_logs_basis; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_activity_logs_basis ON master.activity_logs USING btree (processing_lawful_basis);


--
-- TOC entry 3720 (class 1259 OID 86554)
-- Name: idx_activity_logs_ip; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_activity_logs_ip ON master.activity_logs USING btree (ip_address);


--
-- TOC entry 3721 (class 1259 OID 86555)
-- Name: idx_activity_logs_sensitivity; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_activity_logs_sensitivity ON master.activity_logs USING btree (data_sensitivity_level);


--
-- TOC entry 3722 (class 1259 OID 86556)
-- Name: idx_activity_logs_session; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_activity_logs_session ON master.activity_logs USING btree (session_id);


--
-- TOC entry 3731 (class 1259 OID 86557)
-- Name: idx_addresses_api_data_gin; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_api_data_gin ON master.addresses USING gin (api_data);


--
-- TOC entry 3732 (class 1259 OID 86558)
-- Name: idx_addresses_area_code; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_area_code ON master.addresses USING btree (area_code);


--
-- TOC entry 3733 (class 1259 OID 86559)
-- Name: idx_addresses_city_state; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_city_state ON master.addresses USING btree (city, state);


--
-- TOC entry 3734 (class 1259 OID 86560)
-- Name: idx_addresses_coordinates; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_coordinates ON master.addresses USING btree (latitude, longitude) WHERE ((latitude IS NOT NULL) AND (longitude IS NOT NULL));


--
-- TOC entry 3735 (class 1259 OID 86561)
-- Name: idx_addresses_coverage; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_coverage ON master.addresses USING btree (within_coverage);


--
-- TOC entry 3736 (class 1259 OID 86562)
-- Name: idx_addresses_deleted_at; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_deleted_at ON master.addresses USING btree (deleted_at);


--
-- TOC entry 3737 (class 1259 OID 86563)
-- Name: idx_addresses_distance; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_distance ON master.addresses USING btree (distance_to_establishment);


--
-- TOC entry 3738 (class 1259 OID 86564)
-- Name: idx_addresses_google_place_id; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_google_place_id ON master.addresses USING btree (google_place_id);


--
-- TOC entry 3739 (class 1259 OID 86565)
-- Name: idx_addresses_ibge_codes; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_ibge_codes ON master.addresses USING btree (ibge_city_code, ibge_state_code);


--
-- TOC entry 3740 (class 1259 OID 86566)
-- Name: idx_addresses_polymorphic; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_polymorphic ON master.addresses USING btree (addressable_type, addressable_id);


--
-- TOC entry 3741 (class 1259 OID 86567)
-- Name: idx_addresses_principal; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_principal ON master.addresses USING btree (is_principal);


--
-- TOC entry 3742 (class 1259 OID 86568)
-- Name: idx_addresses_quality_score; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_quality_score ON master.addresses USING btree (quality_score);


--
-- TOC entry 3743 (class 1259 OID 86569)
-- Name: idx_addresses_region; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_region ON master.addresses USING btree (region);


--
-- TOC entry 3744 (class 1259 OID 86570)
-- Name: idx_addresses_validated; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_validated ON master.addresses USING btree (is_validated);


--
-- TOC entry 3745 (class 1259 OID 86571)
-- Name: idx_addresses_zip_code; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_addresses_zip_code ON master.addresses USING btree (zip_code);


--
-- TOC entry 3784 (class 1259 OID 86572)
-- Name: idx_consent_explicit; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_consent_explicit ON master.consent_records USING btree (is_explicit_consent);


--
-- TOC entry 3785 (class 1259 OID 86573)
-- Name: idx_consent_interface; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_consent_interface ON master.consent_records USING btree (collection_interface);


--
-- TOC entry 3838 (class 1259 OID 86574)
-- Name: idx_incidents_occurred; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_incidents_occurred ON master.lgpd_incidents USING btree (occurred_at);


--
-- TOC entry 3839 (class 1259 OID 86575)
-- Name: idx_incidents_status; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_incidents_status ON master.lgpd_incidents USING btree (status);


--
-- TOC entry 3840 (class 1259 OID 86576)
-- Name: idx_incidents_type_severity; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_incidents_type_severity ON master.lgpd_incidents USING btree (incident_type, severity);


--
-- TOC entry 3917 (class 1259 OID 86577)
-- Name: idx_query_logs_sensitivity; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_query_logs_sensitivity ON master.query_audit_logs USING btree (data_sensitivity_level);


--
-- TOC entry 3918 (class 1259 OID 86578)
-- Name: idx_query_logs_table_time; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_query_logs_table_time ON master.query_audit_logs USING btree (table_accessed, "timestamp");


--
-- TOC entry 3919 (class 1259 OID 86579)
-- Name: idx_query_logs_timestamp; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_query_logs_timestamp ON master.query_audit_logs USING btree ("timestamp");


--
-- TOC entry 3920 (class 1259 OID 86580)
-- Name: idx_query_logs_user_time; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_query_logs_user_time ON master.query_audit_logs USING btree (user_id, "timestamp");


--
-- TOC entry 3982 (class 1259 OID 87845)
-- Name: idx_user_establishments_deleted_at; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_user_establishments_deleted_at ON master.user_establishments USING btree (deleted_at);


--
-- TOC entry 3983 (class 1259 OID 87843)
-- Name: idx_user_establishments_establishment_id; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_user_establishments_establishment_id ON master.user_establishments USING btree (establishment_id) WHERE (deleted_at IS NULL);


--
-- TOC entry 3984 (class 1259 OID 87846)
-- Name: idx_user_establishments_primary; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_user_establishments_primary ON master.user_establishments USING btree (user_id, is_primary) WHERE ((is_primary = true) AND (deleted_at IS NULL));


--
-- TOC entry 3985 (class 1259 OID 87844)
-- Name: idx_user_establishments_status; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_user_establishments_status ON master.user_establishments USING btree (status) WHERE (deleted_at IS NULL);


--
-- TOC entry 3986 (class 1259 OID 87842)
-- Name: idx_user_establishments_user_id; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX idx_user_establishments_user_id ON master.user_establishments USING btree (user_id) WHERE (deleted_at IS NULL);


--
-- TOC entry 3746 (class 1259 OID 86581)
-- Name: master_addresses_deleted_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX master_addresses_deleted_at_index ON master.addresses USING btree (deleted_at);


--
-- TOC entry 3832 (class 1259 OID 86582)
-- Name: master_jobs_queue_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX master_jobs_queue_index ON master.jobs USING btree (queue);


--
-- TOC entry 3835 (class 1259 OID 86583)
-- Name: master_lgpd_audit_config_table_name_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX master_lgpd_audit_config_table_name_index ON master.lgpd_audit_config USING btree (table_name);


--
-- TOC entry 3921 (class 1259 OID 86584)
-- Name: master_query_audit_logs_session_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX master_query_audit_logs_session_id_index ON master.query_audit_logs USING btree (session_id);


--
-- TOC entry 3922 (class 1259 OID 86585)
-- Name: master_query_audit_logs_table_accessed_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX master_query_audit_logs_table_accessed_index ON master.query_audit_logs USING btree (table_accessed);


--
-- TOC entry 3923 (class 1259 OID 86586)
-- Name: master_query_audit_logs_user_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX master_query_audit_logs_user_id_index ON master.query_audit_logs USING btree (user_id);


--
-- TOC entry 3845 (class 1259 OID 86587)
-- Name: menus_allowed_companies_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_allowed_companies_fulltext ON master.menus USING gin (to_tsvector('english'::regconfig, allowed_companies));


--
-- TOC entry 3846 (class 1259 OID 86588)
-- Name: menus_allowed_establishments_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_allowed_establishments_fulltext ON master.menus USING gin (to_tsvector('english'::regconfig, allowed_establishments));


--
-- TOC entry 3847 (class 1259 OID 86589)
-- Name: menus_deleted_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_deleted_at_index ON master.menus USING btree (deleted_at);


--
-- TOC entry 3848 (class 1259 OID 86590)
-- Name: menus_dev_only_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_dev_only_index ON master.menus USING btree (dev_only);


--
-- TOC entry 3849 (class 1259 OID 86591)
-- Name: menus_is_active_is_visible_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_is_active_is_visible_index ON master.menus USING btree (is_active, is_visible);


--
-- TOC entry 3850 (class 1259 OID 86592)
-- Name: menus_level_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_level_index ON master.menus USING btree (level);


--
-- TOC entry 3851 (class 1259 OID 86593)
-- Name: menus_level_sort_order_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_level_sort_order_index ON master.menus USING btree (level, sort_order);


--
-- TOC entry 3852 (class 1259 OID 86594)
-- Name: menus_parent_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_parent_id_index ON master.menus USING btree (parent_id);


--
-- TOC entry 3853 (class 1259 OID 86595)
-- Name: menus_parent_id_sort_order_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_parent_id_sort_order_index ON master.menus USING btree (parent_id, sort_order);


--
-- TOC entry 3854 (class 1259 OID 86596)
-- Name: menus_path_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_path_index ON master.menus USING btree (path);


--
-- TOC entry 3855 (class 1259 OID 86597)
-- Name: menus_permission_name_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_permission_name_index ON master.menus USING btree (permission_name);


--
-- TOC entry 3858 (class 1259 OID 86598)
-- Name: menus_required_permissions_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_required_permissions_fulltext ON master.menus USING gin (to_tsvector('english'::regconfig, required_permissions));


--
-- TOC entry 3859 (class 1259 OID 86599)
-- Name: menus_required_roles_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_required_roles_fulltext ON master.menus USING gin (to_tsvector('english'::regconfig, required_roles));


--
-- TOC entry 3860 (class 1259 OID 86600)
-- Name: menus_route_name_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_route_name_index ON master.menus USING btree (route_name);


--
-- TOC entry 3863 (class 1259 OID 86601)
-- Name: menus_sort_order_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_sort_order_index ON master.menus USING btree (sort_order);


--
-- TOC entry 3864 (class 1259 OID 86602)
-- Name: menus_visible_in_menu_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX menus_visible_in_menu_index ON master.menus USING btree (visible_in_menu);


--
-- TOC entry 3869 (class 1259 OID 86603)
-- Name: people_deleted_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX people_deleted_at_index ON master.people USING btree (deleted_at);


--
-- TOC entry 3870 (class 1259 OID 86604)
-- Name: people_metadata_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX people_metadata_fulltext ON master.people USING gin (to_tsvector('english'::regconfig, metadata));


--
-- TOC entry 3871 (class 1259 OID 86605)
-- Name: people_name_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX people_name_index ON master.people USING btree (name);


--
-- TOC entry 3872 (class 1259 OID 86606)
-- Name: people_person_type_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX people_person_type_index ON master.people USING btree (person_type);


--
-- TOC entry 3875 (class 1259 OID 86607)
-- Name: people_status_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX people_status_index ON master.people USING btree (status);


--
-- TOC entry 3878 (class 1259 OID 86608)
-- Name: permissions_context_level_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX permissions_context_level_index ON master.permissions USING btree (context_level);


--
-- TOC entry 3879 (class 1259 OID 86609)
-- Name: permissions_is_active_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX permissions_is_active_index ON master.permissions USING btree (is_active);


--
-- TOC entry 3880 (class 1259 OID 86610)
-- Name: permissions_module_action_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX permissions_module_action_index ON master.permissions USING btree (module, action);


--
-- TOC entry 3883 (class 1259 OID 86611)
-- Name: permissions_module_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX permissions_module_index ON master.permissions USING btree (module);


--
-- TOC entry 3884 (class 1259 OID 86612)
-- Name: permissions_name_is_active_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX permissions_name_is_active_index ON master.permissions USING btree (name, is_active);


--
-- TOC entry 3889 (class 1259 OID 86613)
-- Name: phones_accepts_whatsapp_marketing_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX phones_accepts_whatsapp_marketing_index ON master.phones USING btree (accepts_whatsapp_marketing);


--
-- TOC entry 3890 (class 1259 OID 86614)
-- Name: phones_api_data_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX phones_api_data_fulltext ON master.phones USING gin (to_tsvector('english'::regconfig, api_data));


--
-- TOC entry 3891 (class 1259 OID 86615)
-- Name: phones_carrier_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX phones_carrier_index ON master.phones USING btree (carrier);


--
-- TOC entry 3892 (class 1259 OID 86616)
-- Name: phones_deleted_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX phones_deleted_at_index ON master.phones USING btree (deleted_at);


--
-- TOC entry 3893 (class 1259 OID 86617)
-- Name: phones_is_whatsapp_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX phones_is_whatsapp_index ON master.phones USING btree (is_whatsapp);


--
-- TOC entry 3894 (class 1259 OID 86618)
-- Name: phones_number_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX phones_number_index ON master.phones USING btree (number);


--
-- TOC entry 3895 (class 1259 OID 86619)
-- Name: phones_phoneable_type_phoneable_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX phones_phoneable_type_phoneable_id_index ON master.phones USING btree (phoneable_type, phoneable_id);


--
-- TOC entry 3896 (class 1259 OID 86620)
-- Name: phones_phoneable_type_phoneable_id_whatsapp_formatted_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX phones_phoneable_type_phoneable_id_whatsapp_formatted_index ON master.phones USING btree (phoneable_type, phoneable_id, whatsapp_formatted);


--
-- TOC entry 3899 (class 1259 OID 86621)
-- Name: phones_verified_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX phones_verified_at_index ON master.phones USING btree (verified_at);


--
-- TOC entry 3900 (class 1259 OID 86622)
-- Name: phones_whatsapp_business_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX phones_whatsapp_business_index ON master.phones USING btree (whatsapp_business);


--
-- TOC entry 3901 (class 1259 OID 86623)
-- Name: phones_whatsapp_formatted_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX phones_whatsapp_formatted_index ON master.phones USING btree (whatsapp_formatted);


--
-- TOC entry 3902 (class 1259 OID 86624)
-- Name: phones_whatsapp_verified_whatsapp_verified_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX phones_whatsapp_verified_whatsapp_verified_at_index ON master.phones USING btree (whatsapp_verified, whatsapp_verified_at);


--
-- TOC entry 3903 (class 1259 OID 86625)
-- Name: professionals_deleted_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX professionals_deleted_at_index ON master.professionals USING btree (deleted_at);


--
-- TOC entry 3904 (class 1259 OID 86626)
-- Name: professionals_establishment_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX professionals_establishment_id_index ON master.professionals USING btree (establishment_id);


--
-- TOC entry 3907 (class 1259 OID 86627)
-- Name: professionals_pf_person_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX professionals_pf_person_id_index ON master.professionals USING btree (pf_person_id);


--
-- TOC entry 3910 (class 1259 OID 86628)
-- Name: professionals_pj_person_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX professionals_pj_person_id_index ON master.professionals USING btree (pj_person_id);


--
-- TOC entry 3915 (class 1259 OID 86629)
-- Name: professionals_specialties_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX professionals_specialties_fulltext ON master.professionals USING gin (to_tsvector('english'::regconfig, specialties));


--
-- TOC entry 3916 (class 1259 OID 86630)
-- Name: professionals_status_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX professionals_status_index ON master.professionals USING btree (status);


--
-- TOC entry 3926 (class 1259 OID 86631)
-- Name: role_permissions_granted_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX role_permissions_granted_at_index ON master.role_permissions USING btree (granted_at);


--
-- TOC entry 3927 (class 1259 OID 86632)
-- Name: role_permissions_granted_by_user_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX role_permissions_granted_by_user_id_index ON master.role_permissions USING btree (granted_by_user_id);


--
-- TOC entry 3928 (class 1259 OID 86633)
-- Name: role_permissions_permission_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX role_permissions_permission_id_index ON master.role_permissions USING btree (permission_id);


--
-- TOC entry 3931 (class 1259 OID 86634)
-- Name: role_permissions_role_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX role_permissions_role_id_index ON master.role_permissions USING btree (role_id);


--
-- TOC entry 3934 (class 1259 OID 86635)
-- Name: roles_context_type_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX roles_context_type_index ON master.roles USING btree (context_type);


--
-- TOC entry 3935 (class 1259 OID 86636)
-- Name: roles_is_active_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX roles_is_active_index ON master.roles USING btree (is_active);


--
-- TOC entry 3936 (class 1259 OID 86637)
-- Name: roles_is_system_role_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX roles_is_system_role_index ON master.roles USING btree (is_system_role);


--
-- TOC entry 3937 (class 1259 OID 86638)
-- Name: roles_level_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX roles_level_index ON master.roles USING btree (level);


--
-- TOC entry 3938 (class 1259 OID 86639)
-- Name: roles_name_is_active_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX roles_name_is_active_index ON master.roles USING btree (name, is_active);


--
-- TOC entry 3943 (class 1259 OID 86640)
-- Name: roles_settings_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX roles_settings_fulltext ON master.roles USING gin (to_tsvector('english'::regconfig, settings));


--
-- TOC entry 3944 (class 1259 OID 86641)
-- Name: sessions_last_activity_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX sessions_last_activity_index ON master.sessions USING btree (last_activity);


--
-- TOC entry 3947 (class 1259 OID 86642)
-- Name: sessions_user_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX sessions_user_id_index ON master.sessions USING btree (user_id);


--
-- TOC entry 3948 (class 1259 OID 86643)
-- Name: tenant_features_expires_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX tenant_features_expires_at_index ON master.tenant_features USING btree (expires_at);


--
-- TOC entry 3949 (class 1259 OID 86644)
-- Name: tenant_features_feature_config_fulltext; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX tenant_features_feature_config_fulltext ON master.tenant_features USING gin (to_tsvector('english'::regconfig, feature_config));


--
-- TOC entry 3950 (class 1259 OID 86645)
-- Name: tenant_features_feature_key_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX tenant_features_feature_key_index ON master.tenant_features USING btree (feature_key);


--
-- TOC entry 3955 (class 1259 OID 86646)
-- Name: tenant_features_tenant_type_tenant_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX tenant_features_tenant_type_tenant_id_index ON master.tenant_features USING btree (tenant_type, tenant_id);


--
-- TOC entry 3956 (class 1259 OID 86647)
-- Name: tenant_features_tenant_type_tenant_id_is_enabled_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX tenant_features_tenant_type_tenant_id_is_enabled_index ON master.tenant_features USING btree (tenant_type, tenant_id, is_enabled);


--
-- TOC entry 3957 (class 1259 OID 86648)
-- Name: user_contexts_context_type_context_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX user_contexts_context_type_context_id_index ON master.user_contexts USING btree (context_type, context_id);


--
-- TOC entry 3960 (class 1259 OID 86649)
-- Name: user_contexts_session_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX user_contexts_session_id_index ON master.user_contexts USING btree (session_id);


--
-- TOC entry 3961 (class 1259 OID 86650)
-- Name: user_contexts_switched_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX user_contexts_switched_at_index ON master.user_contexts USING btree (switched_at);


--
-- TOC entry 3962 (class 1259 OID 86651)
-- Name: user_contexts_user_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX user_contexts_user_id_index ON master.user_contexts USING btree (user_id);


--
-- TOC entry 3963 (class 1259 OID 86652)
-- Name: user_contexts_user_id_session_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX user_contexts_user_id_session_id_index ON master.user_contexts USING btree (user_id, session_id);


--
-- TOC entry 3964 (class 1259 OID 86653)
-- Name: user_roles_context_type_context_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX user_roles_context_type_context_id_index ON master.user_roles USING btree (context_type, context_id);


--
-- TOC entry 3965 (class 1259 OID 86654)
-- Name: user_roles_deleted_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX user_roles_deleted_at_index ON master.user_roles USING btree (deleted_at);


--
-- TOC entry 3968 (class 1259 OID 86655)
-- Name: user_roles_role_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX user_roles_role_id_index ON master.user_roles USING btree (role_id);


--
-- TOC entry 3969 (class 1259 OID 86656)
-- Name: user_roles_user_id_context_type_context_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX user_roles_user_id_context_type_context_id_index ON master.user_roles USING btree (user_id, context_type, context_id);


--
-- TOC entry 3970 (class 1259 OID 86657)
-- Name: user_roles_user_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX user_roles_user_id_index ON master.user_roles USING btree (user_id);


--
-- TOC entry 3973 (class 1259 OID 86658)
-- Name: users_deleted_at_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX users_deleted_at_index ON master.users USING btree (deleted_at);


--
-- TOC entry 3976 (class 1259 OID 86659)
-- Name: users_is_system_admin_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX users_is_system_admin_index ON master.users USING btree (is_system_admin);


--
-- TOC entry 3977 (class 1259 OID 86660)
-- Name: users_person_id_index; Type: INDEX; Schema: master; Owner: postgres
--

CREATE INDEX users_person_id_index ON master.users USING btree (person_id);


--
-- TOC entry 3991 (class 1259 OID 94128)
-- Name: sessions_last_activity_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX sessions_last_activity_index ON public.sessions USING btree (last_activity);


--
-- TOC entry 3994 (class 1259 OID 94127)
-- Name: sessions_user_id_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX sessions_user_id_index ON public.sessions USING btree (user_id);


--
-- TOC entry 4029 (class 2620 OID 86661)
-- Name: addresses tr_addresses_quality_score; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_addresses_quality_score BEFORE INSERT OR UPDATE ON master.addresses FOR EACH ROW EXECUTE FUNCTION master.fn_addresses_quality_score();


--
-- TOC entry 4030 (class 2620 OID 86662)
-- Name: addresses tr_addresses_single_principal; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_addresses_single_principal BEFORE INSERT OR UPDATE ON master.addresses FOR EACH ROW EXECUTE FUNCTION master.fn_check_single_principal_address();


--
-- TOC entry 4031 (class 2620 OID 86663)
-- Name: addresses tr_addresses_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_addresses_update_timestamp BEFORE UPDATE ON master.addresses FOR EACH ROW EXECUTE FUNCTION master.fn_update_addresses_timestamp();


--
-- TOC entry 4032 (class 2620 OID 86664)
-- Name: addresses tr_addresses_validate_coordinates; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_addresses_validate_coordinates BEFORE INSERT OR UPDATE ON master.addresses FOR EACH ROW WHEN (((new.latitude IS NOT NULL) OR (new.longitude IS NOT NULL))) EXECUTE FUNCTION master.fn_validate_coordinates();


--
-- TOC entry 4034 (class 2620 OID 86665)
-- Name: clients tr_clients_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_clients_update_timestamp BEFORE UPDATE ON master.clients FOR EACH ROW EXECUTE FUNCTION master.fn_update_clients_timestamp();


--
-- TOC entry 4036 (class 2620 OID 86666)
-- Name: companies tr_companies_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_companies_update_timestamp BEFORE UPDATE ON master.companies FOR EACH ROW EXECUTE FUNCTION master.fn_update_companies_timestamp();


--
-- TOC entry 4038 (class 2620 OID 86667)
-- Name: company_settings tr_company_settings_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_company_settings_update_timestamp BEFORE UPDATE ON master.company_settings FOR EACH ROW EXECUTE FUNCTION master.fn_update_company_settings_timestamp();


--
-- TOC entry 4039 (class 2620 OID 86668)
-- Name: consent_records tr_consent_records_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_consent_records_update_timestamp BEFORE UPDATE ON master.consent_records FOR EACH ROW EXECUTE FUNCTION master.fn_update_consent_records_timestamp();


--
-- TOC entry 4040 (class 2620 OID 86669)
-- Name: documents tr_documents_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_documents_update_timestamp BEFORE UPDATE ON master.documents FOR EACH ROW EXECUTE FUNCTION master.fn_update_documents_timestamp();


--
-- TOC entry 4041 (class 2620 OID 86670)
-- Name: emails tr_emails_single_principal; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_emails_single_principal BEFORE INSERT OR UPDATE ON master.emails FOR EACH ROW EXECUTE FUNCTION master.fn_check_single_principal_email();


--
-- TOC entry 4042 (class 2620 OID 86671)
-- Name: emails tr_emails_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_emails_update_timestamp BEFORE UPDATE ON master.emails FOR EACH ROW EXECUTE FUNCTION master.fn_update_emails_timestamp();


--
-- TOC entry 4044 (class 2620 OID 86672)
-- Name: establishment_settings tr_establishment_settings_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_establishment_settings_update_timestamp BEFORE UPDATE ON master.establishment_settings FOR EACH ROW EXECUTE FUNCTION master.fn_update_establishment_settings_timestamp();


--
-- TOC entry 4045 (class 2620 OID 86673)
-- Name: establishments tr_establishments_single_principal; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_establishments_single_principal BEFORE INSERT OR UPDATE ON master.establishments FOR EACH ROW EXECUTE FUNCTION master.fn_check_single_principal_establishment();


--
-- TOC entry 4046 (class 2620 OID 86674)
-- Name: establishments tr_establishments_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_establishments_update_timestamp BEFORE UPDATE ON master.establishments FOR EACH ROW EXECUTE FUNCTION master.fn_update_establishments_timestamp();


--
-- TOC entry 4033 (class 2620 OID 86675)
-- Name: addresses tr_lgpd_audit_addresses; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_lgpd_audit_addresses AFTER INSERT OR DELETE OR UPDATE ON master.addresses FOR EACH ROW EXECUTE FUNCTION master.fn_lgpd_automatic_audit();


--
-- TOC entry 4035 (class 2620 OID 86676)
-- Name: clients tr_lgpd_audit_clients; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_lgpd_audit_clients AFTER INSERT OR DELETE OR UPDATE ON master.clients FOR EACH ROW EXECUTE FUNCTION master.fn_lgpd_automatic_audit();


--
-- TOC entry 4037 (class 2620 OID 86677)
-- Name: companies tr_lgpd_audit_companies; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_lgpd_audit_companies AFTER INSERT OR DELETE OR UPDATE ON master.companies FOR EACH ROW EXECUTE FUNCTION master.fn_lgpd_automatic_audit();


--
-- TOC entry 4043 (class 2620 OID 86678)
-- Name: emails tr_lgpd_audit_emails; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_lgpd_audit_emails AFTER INSERT OR DELETE OR UPDATE ON master.emails FOR EACH ROW EXECUTE FUNCTION master.fn_lgpd_automatic_audit();


--
-- TOC entry 4049 (class 2620 OID 86679)
-- Name: people tr_lgpd_audit_people; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_lgpd_audit_people AFTER INSERT OR DELETE OR UPDATE ON master.people FOR EACH ROW EXECUTE FUNCTION master.fn_lgpd_automatic_audit();


--
-- TOC entry 4052 (class 2620 OID 86680)
-- Name: phones tr_lgpd_audit_phones; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_lgpd_audit_phones AFTER INSERT OR DELETE OR UPDATE ON master.phones FOR EACH ROW EXECUTE FUNCTION master.fn_lgpd_automatic_audit();


--
-- TOC entry 4056 (class 2620 OID 86681)
-- Name: professionals tr_lgpd_audit_professionals; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_lgpd_audit_professionals AFTER INSERT OR DELETE OR UPDATE ON master.professionals FOR EACH ROW EXECUTE FUNCTION master.fn_lgpd_automatic_audit();


--
-- TOC entry 4063 (class 2620 OID 86682)
-- Name: users tr_lgpd_audit_users; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_lgpd_audit_users AFTER INSERT OR DELETE OR UPDATE ON master.users FOR EACH ROW EXECUTE FUNCTION master.fn_lgpd_automatic_audit();


--
-- TOC entry 4047 (class 2620 OID 86683)
-- Name: menus tr_menus_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_menus_update_timestamp BEFORE UPDATE ON master.menus FOR EACH ROW EXECUTE FUNCTION master.fn_update_menus_timestamp();


--
-- TOC entry 4048 (class 2620 OID 86684)
-- Name: menus tr_menus_validate_hierarchy; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_menus_validate_hierarchy BEFORE INSERT OR UPDATE ON master.menus FOR EACH ROW EXECUTE FUNCTION master.fn_validate_menu_hierarchy();


--
-- TOC entry 4050 (class 2620 OID 86685)
-- Name: people tr_people_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_people_update_timestamp BEFORE UPDATE ON master.people FOR EACH ROW EXECUTE FUNCTION master.fn_update_people_timestamp();


--
-- TOC entry 4051 (class 2620 OID 86686)
-- Name: permissions tr_permissions_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_permissions_update_timestamp BEFORE UPDATE ON master.permissions FOR EACH ROW EXECUTE FUNCTION master.fn_update_permissions_timestamp();


--
-- TOC entry 4053 (class 2620 OID 86687)
-- Name: phones tr_phones_format_whatsapp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_phones_format_whatsapp BEFORE INSERT OR UPDATE ON master.phones FOR EACH ROW EXECUTE FUNCTION master.fn_phones_format_whatsapp();


--
-- TOC entry 4054 (class 2620 OID 86688)
-- Name: phones tr_phones_single_principal; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_phones_single_principal BEFORE INSERT OR UPDATE ON master.phones FOR EACH ROW EXECUTE FUNCTION master.fn_check_single_principal_phone();


--
-- TOC entry 4055 (class 2620 OID 86689)
-- Name: phones tr_phones_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_phones_update_timestamp BEFORE UPDATE ON master.phones FOR EACH ROW EXECUTE FUNCTION master.fn_update_phones_timestamp();


--
-- TOC entry 4057 (class 2620 OID 86690)
-- Name: professionals tr_professionals_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_professionals_update_timestamp BEFORE UPDATE ON master.professionals FOR EACH ROW EXECUTE FUNCTION master.fn_update_professionals_timestamp();


--
-- TOC entry 4058 (class 2620 OID 86691)
-- Name: role_permissions tr_role_permissions_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_role_permissions_update_timestamp BEFORE UPDATE ON master.role_permissions FOR EACH ROW EXECUTE FUNCTION master.fn_update_role_permissions_timestamp();


--
-- TOC entry 4059 (class 2620 OID 86692)
-- Name: roles tr_roles_protect_system; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_roles_protect_system BEFORE UPDATE ON master.roles FOR EACH ROW EXECUTE FUNCTION master.fn_protect_system_roles();


--
-- TOC entry 4060 (class 2620 OID 86693)
-- Name: roles tr_roles_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_roles_update_timestamp BEFORE UPDATE ON master.roles FOR EACH ROW EXECUTE FUNCTION master.fn_update_roles_timestamp();


--
-- TOC entry 4061 (class 2620 OID 86694)
-- Name: tenant_features tr_tenant_features_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_tenant_features_update_timestamp BEFORE UPDATE ON master.tenant_features FOR EACH ROW EXECUTE FUNCTION master.fn_update_tenant_features_timestamp();


--
-- TOC entry 4062 (class 2620 OID 86696)
-- Name: user_roles tr_user_roles_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_user_roles_update_timestamp BEFORE UPDATE ON master.user_roles FOR EACH ROW EXECUTE FUNCTION master.fn_update_user_roles_timestamp();


--
-- TOC entry 4064 (class 2620 OID 86697)
-- Name: users tr_users_password_changed; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_users_password_changed BEFORE UPDATE ON master.users FOR EACH ROW EXECUTE FUNCTION master.fn_users_password_changed();


--
-- TOC entry 4065 (class 2620 OID 86698)
-- Name: users tr_users_update_timestamp; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER tr_users_update_timestamp BEFORE UPDATE ON master.users FOR EACH ROW EXECUTE FUNCTION master.fn_update_users_timestamp();


--
-- TOC entry 4066 (class 2620 OID 87848)
-- Name: user_establishments trigger_user_establishments_updated_at; Type: TRIGGER; Schema: master; Owner: postgres
--

CREATE TRIGGER trigger_user_establishments_updated_at BEFORE UPDATE ON master.user_establishments FOR EACH ROW EXECUTE FUNCTION master.fn_update_user_establishments_timestamp();


--
-- TOC entry 3999 (class 2606 OID 86699)
-- Name: clients fk_clients_establishment; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.clients
    ADD CONSTRAINT fk_clients_establishment FOREIGN KEY (establishment_id) REFERENCES master.establishments(id) ON DELETE CASCADE;


--
-- TOC entry 4000 (class 2606 OID 86704)
-- Name: clients fk_clients_person; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.clients
    ADD CONSTRAINT fk_clients_person FOREIGN KEY (person_id) REFERENCES master.people(id) ON DELETE CASCADE;


--
-- TOC entry 4001 (class 2606 OID 86709)
-- Name: companies fk_companies_person; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.companies
    ADD CONSTRAINT fk_companies_person FOREIGN KEY (person_id) REFERENCES master.people(id) ON DELETE CASCADE;


--
-- TOC entry 4002 (class 2606 OID 86714)
-- Name: company_settings fk_company_settings_company; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.company_settings
    ADD CONSTRAINT fk_company_settings_company FOREIGN KEY (company_id) REFERENCES master.companies(id) ON DELETE CASCADE;


--
-- TOC entry 4003 (class 2606 OID 86719)
-- Name: company_settings fk_company_settings_updated_by; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.company_settings
    ADD CONSTRAINT fk_company_settings_updated_by FOREIGN KEY (updated_by_user_id) REFERENCES master.users(id) ON DELETE SET NULL;


--
-- TOC entry 4004 (class 2606 OID 86724)
-- Name: consent_records fk_consent_records_person; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.consent_records
    ADD CONSTRAINT fk_consent_records_person FOREIGN KEY (person_id) REFERENCES master.people(id) ON DELETE CASCADE;


--
-- TOC entry 4005 (class 2606 OID 86729)
-- Name: documents fk_documents_uploaded_by; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.documents
    ADD CONSTRAINT fk_documents_uploaded_by FOREIGN KEY (uploaded_by_user_id) REFERENCES master.users(id) ON DELETE SET NULL;


--
-- TOC entry 4006 (class 2606 OID 86734)
-- Name: establishment_settings fk_establishment_settings_establishment; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.establishment_settings
    ADD CONSTRAINT fk_establishment_settings_establishment FOREIGN KEY (establishment_id) REFERENCES master.establishments(id) ON DELETE CASCADE;


--
-- TOC entry 4007 (class 2606 OID 86739)
-- Name: establishment_settings fk_establishment_settings_updated_by; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.establishment_settings
    ADD CONSTRAINT fk_establishment_settings_updated_by FOREIGN KEY (updated_by_user_id) REFERENCES master.users(id) ON DELETE SET NULL;


--
-- TOC entry 4008 (class 2606 OID 86744)
-- Name: establishments fk_establishments_company; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.establishments
    ADD CONSTRAINT fk_establishments_company FOREIGN KEY (company_id) REFERENCES master.companies(id) ON DELETE CASCADE;


--
-- TOC entry 4009 (class 2606 OID 86749)
-- Name: establishments fk_establishments_person; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.establishments
    ADD CONSTRAINT fk_establishments_person FOREIGN KEY (person_id) REFERENCES master.people(id) ON DELETE CASCADE;


--
-- TOC entry 4010 (class 2606 OID 86754)
-- Name: lgpd_incidents fk_incidents_user; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.lgpd_incidents
    ADD CONSTRAINT fk_incidents_user FOREIGN KEY (responsible_user_id) REFERENCES master.users(id) ON DELETE SET NULL;


--
-- TOC entry 4011 (class 2606 OID 86759)
-- Name: menus fk_menus_parent; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.menus
    ADD CONSTRAINT fk_menus_parent FOREIGN KEY (parent_id) REFERENCES master.menus(id) ON DELETE CASCADE;


--
-- TOC entry 4012 (class 2606 OID 86764)
-- Name: professionals fk_professionals_establishment; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.professionals
    ADD CONSTRAINT fk_professionals_establishment FOREIGN KEY (establishment_id) REFERENCES master.establishments(id) ON DELETE CASCADE;


--
-- TOC entry 4013 (class 2606 OID 86769)
-- Name: professionals fk_professionals_person_pf; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.professionals
    ADD CONSTRAINT fk_professionals_person_pf FOREIGN KEY (pf_person_id) REFERENCES master.people(id) ON DELETE RESTRICT;


--
-- TOC entry 4014 (class 2606 OID 86774)
-- Name: professionals fk_professionals_person_pj; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.professionals
    ADD CONSTRAINT fk_professionals_person_pj FOREIGN KEY (pj_person_id) REFERENCES master.people(id) ON DELETE SET NULL;


--
-- TOC entry 4015 (class 2606 OID 86779)
-- Name: query_audit_logs fk_query_logs_user; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.query_audit_logs
    ADD CONSTRAINT fk_query_logs_user FOREIGN KEY (user_id) REFERENCES master.users(id) ON DELETE CASCADE;


--
-- TOC entry 4016 (class 2606 OID 86784)
-- Name: role_permissions fk_role_permissions_granted_by; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.role_permissions
    ADD CONSTRAINT fk_role_permissions_granted_by FOREIGN KEY (granted_by_user_id) REFERENCES master.users(id);


--
-- TOC entry 4017 (class 2606 OID 86789)
-- Name: role_permissions fk_role_permissions_permissions; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.role_permissions
    ADD CONSTRAINT fk_role_permissions_permissions FOREIGN KEY (permission_id) REFERENCES master.permissions(id) ON DELETE CASCADE;


--
-- TOC entry 4018 (class 2606 OID 86794)
-- Name: role_permissions fk_role_permissions_roles; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.role_permissions
    ADD CONSTRAINT fk_role_permissions_roles FOREIGN KEY (role_id) REFERENCES master.roles(id) ON DELETE CASCADE;


--
-- TOC entry 4019 (class 2606 OID 86799)
-- Name: tenant_features fk_tenant_features_updated_by; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.tenant_features
    ADD CONSTRAINT fk_tenant_features_updated_by FOREIGN KEY (updated_by_user_id) REFERENCES master.users(id) ON DELETE SET NULL;


--
-- TOC entry 4020 (class 2606 OID 86804)
-- Name: user_contexts fk_user_contexts_user; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_contexts
    ADD CONSTRAINT fk_user_contexts_user FOREIGN KEY (user_id) REFERENCES master.users(id) ON DELETE CASCADE;


--
-- TOC entry 4021 (class 2606 OID 86809)
-- Name: user_roles fk_user_roles_assigned_by; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_roles
    ADD CONSTRAINT fk_user_roles_assigned_by FOREIGN KEY (assigned_by_user_id) REFERENCES master.users(id) ON DELETE SET NULL;


--
-- TOC entry 4022 (class 2606 OID 86814)
-- Name: user_roles fk_user_roles_role; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_roles
    ADD CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES master.roles(id) ON DELETE CASCADE;


--
-- TOC entry 4023 (class 2606 OID 86819)
-- Name: user_roles fk_user_roles_user; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_roles
    ADD CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES master.users(id) ON DELETE CASCADE;


--
-- TOC entry 4024 (class 2606 OID 86824)
-- Name: users fk_users_person; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.users
    ADD CONSTRAINT fk_users_person FOREIGN KEY (person_id) REFERENCES master.people(id) ON DELETE CASCADE;


--
-- TOC entry 4025 (class 2606 OID 87837)
-- Name: user_establishments user_establishments_assigned_by_user_id_fkey; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_establishments
    ADD CONSTRAINT user_establishments_assigned_by_user_id_fkey FOREIGN KEY (assigned_by_user_id) REFERENCES master.users(id);


--
-- TOC entry 4026 (class 2606 OID 87827)
-- Name: user_establishments user_establishments_establishment_id_fkey; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_establishments
    ADD CONSTRAINT user_establishments_establishment_id_fkey FOREIGN KEY (establishment_id) REFERENCES master.establishments(id) ON DELETE CASCADE;


--
-- TOC entry 4027 (class 2606 OID 87832)
-- Name: user_establishments user_establishments_role_id_fkey; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_establishments
    ADD CONSTRAINT user_establishments_role_id_fkey FOREIGN KEY (role_id) REFERENCES master.roles(id);


--
-- TOC entry 4028 (class 2606 OID 87822)
-- Name: user_establishments user_establishments_user_id_fkey; Type: FK CONSTRAINT; Schema: master; Owner: postgres
--

ALTER TABLE ONLY master.user_establishments
    ADD CONSTRAINT user_establishments_user_id_fkey FOREIGN KEY (user_id) REFERENCES master.users(id) ON DELETE CASCADE;


-- Completed on 2025-09-02 17:49:44 -03

--
-- PostgreSQL database dump complete
--
