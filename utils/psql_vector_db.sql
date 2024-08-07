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
-- Name: bedrock_integration; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA bedrock_integration;


ALTER SCHEMA bedrock_integration OWNER TO postgres;

--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat access method';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bedrock_kb; Type: TABLE; Schema: bedrock_integration; Owner: bedrock_user
--

CREATE TABLE bedrock_integration.bedrock_kb (
    id uuid NOT NULL,
    embedding public.vector(1024),
    chunks text,
    metadata json
);


ALTER TABLE bedrock_integration.bedrock_kb OWNER TO bedrock_user;

--
-- Name: bedrock_kb bedrock_kb_pkey; Type: CONSTRAINT; Schema: bedrock_integration; Owner: bedrock_user
--

ALTER TABLE ONLY bedrock_integration.bedrock_kb
    ADD CONSTRAINT bedrock_kb_pkey PRIMARY KEY (id);


--
-- Name: bedrock_kb_embedding_idx; Type: INDEX; Schema: bedrock_integration; Owner: bedrock_user
--

CREATE INDEX bedrock_kb_embedding_idx ON bedrock_integration.bedrock_kb USING hnsw (embedding public.vector_cosine_ops);


--
-- Name: SCHEMA bedrock_integration; Type: ACL; Schema: -; Owner: postgres
--

GRANT ALL ON SCHEMA bedrock_integration TO bedrock_user;
