#!/usr/bin/env python3

###############################################################
# Copyright 2020 Lawrence Livermore National Security, LLC
# (c.f. AUTHORS, NOTICE.LLNS, COPYING)
#
# This file is part of the Flux resource manager framework.
# For details, see https://github.com/flux-framework.
#
# SPDX-License-Identifier: LGPL-3.0
###############################################################
import sqlite3
import argparse
import time
import sys
import pwd
import csv

import pandas as pd


def add_bank(conn, bank, shares, parent_bank=""):
    # if the parent bank is not "", that means the bank
    # trying to be added wants to be placed under a parent bank
    if parent_bank != "":
        try:
            select_stmt = "SELECT shares FROM bank_table where bank=?"
            dataframe = pd.read_sql_query(select_stmt, conn, params=(parent_bank,))
            # if length of dataframe is 0, that means the parent bank wasn't found
            if len(dataframe.index) == 0:
                raise Exception("Parent bank not found in bank table")
        except pd.io.sql.DatabaseError as e_database_error:
            print(e_database_error)

    # insert the bank values into the database
    try:
        conn.execute(
            """
            INSERT INTO bank_table (
                bank,
                parent_bank,
                shares
            )
            VALUES (?, ?, ?)
            """,
            (bank, parent_bank, shares),
        )
        # commit changes
        conn.commit()
    # make sure entry is unique
    except sqlite3.IntegrityError as integrity_error:
        print(integrity_error)


def view_bank(conn, bank):
    try:
        # get the information pertaining to a bank in the Accounting DB
        select_stmt = "SELECT * FROM bank_table where bank=?"
        dataframe = pd.read_sql_query(select_stmt, conn, params=(bank,))
        # if the length of dataframe is 0, that means
        # the bank specified was not found in the table
        if len(dataframe.index) == 0:
            print("Bank not found in bank_table")
        else:
            print(dataframe)
    except pd.io.sql.DatabaseError as e_database_error:
        print(e_database_error)


def delete_bank(conn, bank):
    last_parent_bank_seen = bank

    # delete bank from bank_table
    delete_stmt = "DELETE FROM bank_table WHERE bank=?"
    cursor = conn.cursor()
    cursor.execute(delete_stmt, (bank,))

    # commit changes
    conn.commit()


def edit_bank(conn, bank, shares):
    print(shares)
    # if user tries to edit a shares value <= 0,
    # raise an exception
    if shares <= 0:
        raise Exception("New shares amount must be >= 0")
    try:
        # edit value in bank_table
        conn.execute(
            "UPDATE bank_table SET shares=? WHERE bank=?", (shares, bank,),
        )
        # commit changes
        conn.commit()
    except pd.io.sql.DatabaseError as e_database_error:
        print(e_database_error)


def view_user(conn, user):
    try:
        # get the information pertaining to a user in the Accounting DB
        select_stmt = "SELECT * FROM association_table where user_name=?"
        dataframe = pd.read_sql_query(select_stmt, conn, params=(user,))
        # if the length of dataframe is 0, that means
        # the user specified was not found in the table
        if len(dataframe.index) == 0:
            print("User not found in association_table")
        else:
            print(dataframe)
    except pd.io.sql.DatabaseError as e_database_error:
        print(e_database_error)


def add_user(conn, username, bank, admin_level=1, shares=1, max_jobs=1, max_wall_pj=60):

    # insert the user values into the database
    try:
        conn.execute(
            """
            INSERT INTO association_table (
                creation_time,
                mod_time,
                deleted,
                user_name,
                admin_level,
                bank,
                shares,
                max_jobs,
                max_wall_pj
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(time.time()),
                int(time.time()),
                0,
                username,
                admin_level,
                bank,
                shares,
                max_jobs,
                max_wall_pj,
            ),
        )
        # commit changes
        conn.commit()
    # make sure entry is unique
    except sqlite3.IntegrityError as integrity_error:
        print(integrity_error)


def delete_user(conn, user):
    # delete user account from association_table
    delete_stmt = "DELETE FROM association_table WHERE user_name=?"
    cursor = conn.cursor()
    cursor.execute(delete_stmt, (user,))
    # commit changes
    conn.commit()


def edit_user(conn, username, field, new_value):
    fields = [
        "user_name",
        "admin_level",
        "bank",
        "shares",
        "max_jobs",
        "max_wall_pj",
    ]
    if field in fields:
        the_field = field
    else:
        print("Field not found in association table")
        sys.exit(1)

    # edit value in accounting database
    conn.execute(
        "UPDATE association_table SET " + the_field + "=? WHERE user_name=?",
        (new_value, username,),
    )
    # commit changes
    conn.commit()
