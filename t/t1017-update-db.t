#!/bin/bash

test_description='Test flux account-update-db command'
. `dirname $0`/sharness.sh

DB_PATHv1=$(pwd)/FluxAccountingTestv1.db
DB_PATHv2=$(pwd)/FluxAccountingTestv2.db
MODIFY_DB=${SHARNESS_TEST_SRCDIR}/scripts/modify_accounting_db.py
CHECK_TABLES=${SHARNESS_TEST_SRCDIR}/scripts/check_db_info.py
DB_INTEGRITY_CHECK=${SHARNESS_TEST_SRCDIR}/scripts/db_integrity_check.py

test_expect_success 'create a flux-accounting DB' '
	flux account -p $(pwd)/FluxAccountingTestv1.db create-db
'

test_expect_success 'add some banks to the DB' '
	flux account -p ${DB_PATHv1} add-bank root 1 &&
	flux account -p ${DB_PATHv1} add-bank --parent-bank=root A 1 &&
	flux account -p ${DB_PATHv1} add-bank --parent-bank=root B 1 &&
	flux account -p ${DB_PATHv1} add-bank --parent-bank=root C 1 &&
	flux account -p ${DB_PATHv1} add-bank --parent-bank=root D 1 &&
	flux account -p ${DB_PATHv1} add-bank --parent-bank=D E 1 &&
	flux account -p ${DB_PATHv1} add-bank --parent-bank=D F 1
'

test_expect_success 'add some users to the DB' '
	flux account -p ${DB_PATHv1} add-user --username=user5011 --userid=5011 --bank=A &&
	flux account -p ${DB_PATHv1} add-user --username=user5012 --userid=5012 --bank=A &&
	flux account -p ${DB_PATHv1} add-user --username=user5013 --userid=5013 --bank=B &&
	flux account -p ${DB_PATHv1} add-user --username=user5014 --userid=5014 --bank=C
'

test_expect_success 'create a new flux-accounting DB with an additional table, additional columns in existing tables, and a removed column' '
	flux python ${MODIFY_DB} ${DB_PATHv2}
'

test_expect_success 'run flux account-update-db' '
	flux account-update-db -p ${DB_PATHv1} --new-db ${DB_PATHv2}
'

test_expect_success 'get all the tables of the old DB and check that new table was added' '
	flux python ${CHECK_TABLES} -p ${DB_PATHv1} -t > tables.test &&
	cat <<-EOF >tables.expected
	sqlite_sequence
	association_table
	bank_table
	job_usage_factor_table
	t_half_life_period_table
	project_table
	organization
	queue_table
	EOF
	test_cmp tables.expected tables.test
'

test_expect_success 'get all the columns of the updated table in the DB and check that new columns were added' '
	flux python ${CHECK_TABLES} -p ${DB_PATHv1} -c association_table > association_table_columns.test &&
	cat <<-EOF >association_table_columns.expected
	table name: association_table
	creation_time
	mod_time
	active
	username
	userid
	bank
	default_bank
	shares
	job_usage
	fairshare
	max_running_jobs
	max_active_jobs
	max_nodes
	queues
	projects
	default_project
	organization
	yrs_experience
	EOF
	test_cmp association_table_columns.expected association_table_columns.test
'

test_expect_success 'get all the columns from the queue_table and make sure the dropped column does not show up' '
	flux python ${CHECK_TABLES} -p ${DB_PATHv1} -c queue_table > queue_table_columns.test &&
	cat <<-EOF >queue_table_columns.expected
	table name: queue_table
	queue
	min_nodes_per_job
	max_nodes_per_job
	priority
	EOF
	test_cmp queue_table_columns.expected queue_table_columns.test
'

# test updating flux-accounting databases from older versions,
# starting with v0.10.0
for db in ${SHARNESS_TEST_SRCDIR}/expected/test_dbs/*; do
	if [[ $db == *FluxAccounting* ]]; then
		tmp_db=$(basename $db | cut -d '.' -f 1)_tmp.db
		cp $db $tmp_db
		chmod +rw $tmp_db
		test_expect_success 'update old DB: '$(basename $db) \
			"flux account-update-db -p $tmp_db"
		test_expect_success 'add a bank: '$(basename $db) \
			"flux account -p $tmp_db add-bank root 1"
		test_expect_success 'add a user: '$(basename $db) \
			"flux account -p $tmp_db add-user --username=fluxuser --bank=root"
		test_expect_success 'check validity of DB: '$(basename $db) \
			"flux python ${DB_INTEGRITY_CHECK} $tmp_db > result.out && grep 'ok' result.out"
	fi
done

test_done
