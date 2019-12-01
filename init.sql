create user keepthetips with login password 'u6^o4en$8I6m';
create schema if not exists keepthetips;
drop table if exists keepthetips.submissions;
create table if not exists keepthetips.submissions
(
	id text not null
		constraint id
			primary key,
	commentid text,
	author varchar(22),
	submitted_timestamp timestamp(4) with time zone,
	removed_timestamp timestamp(4) with time zone,
	submitted double precision,
	submission_removed boolean default false,
	comment_removed boolean default false,
	safe boolean default false
);

alter table keepthetips.submissions owner to keepthetips;
alter schema keepthetips owner to keepthetips;