DROP TABLE IF EXISTS "tasks";
DROP SEQUENCE IF EXISTS tasks_id_seq;
CREATE SEQUENCE tasks_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1;
CREATE TABLE "public"."tasks" (
    "id" integer DEFAULT nextval('tasks_id_seq') NOT NULL,
    "content" text NOT NULL,
    "createdAt" time without time zone NOT NULL,
    "completedAt" time without time zone,
    "completed" boolean DEFAULT false NOT NULL,
    "user_id" character(36) NOT NULL,
    "updatedAt" time without time zone,
    CONSTRAINT "tasks_pkey" PRIMARY KEY ("id")
) WITH (oids = false);
COMMENT ON COLUMN "public"."tasks"."user_id" IS 'UUID V4';
DROP TABLE IF EXISTS "users";
CREATE TABLE "public"."users" (
    "id" character(36) NOT NULL,
    "firstname" character varying(32) NOT NULL,
    "lastname" character varying(32) NOT NULL,
    "email" character varying(32) NOT NULL,
    "password" character varying NOT NULL,
    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
) WITH (oids = false);
COMMENT ON COLUMN "public"."users"."id" IS 'UUID V4';
ALTER TABLE ONLY "public"."tasks"
ADD CONSTRAINT "tasks_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE NOT DEFERRABLE;