"""
Quick smoke test for PDS insertion paths (voluntary work, training, other info, declarations).
Runs against the configured database and prints the rows inserted for the newest personal_info_id.
Usage:
    conda activate tf
    python scripts/pds_insert_smoke.py
"""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app
from db import get_db_cursor
from datetime import datetime


def run_smoke():
    payload = {
        # Minimal personal info
        'surname': 'TESTSUR',
        'first_name': 'VOLTRAIN',
        'date_of_birth': '1990-01-01',
        # Voluntary work (2 rows)
        'voluntary_organization[]': ['VOL_ORG_A', 'VOL_ORG_B'],
        'voluntary_period_from[]': ['2020-01-01', '2021-02-01'],
        'voluntary_period_to[]': ['2020-02-01', 'PRESENT'],
        'voluntary_hours[]': ['8', '16'],
        'voluntary_position[]': ['HELPER', 'LEAD'],
        # Training (1 row)
        'training_title[]': ['TRAIN_TITLE'],
        'training_period_from[]': ['2022-03-01'],
        'training_period_to[]': ['2022-03-05'],
        'training_hours[]': ['24'],
        'training_type[]': ['TECH'],
        'training_sponsor[]': ['SPONSOR INC'],
        # Other info
        'skills_hobbies': 'SKILL1, SKILL2',
        'distinctions': 'AWARD1',
        'memberships': 'ORG1, ORG2',
        # Declarations
        'decl_related_3rd': 'Relative 3rd',
        'decl_related_4th': 'Relative 4th',
        'decl_admin_offense': 'None',
        'decl_criminal_charge': 'No',
        'decl_criminal_date': '2023-01-01',
        'decl_criminal_status': 'Closed',
        'decl_conviction': 'None',
        'decl_separation': 'None',
        'decl_election': 'No',
        'decl_resignation_campaign': 'No',
        'decl_immigrant_country': 'N/A',
        'decl_indigenous_group': 'N/A',
        'decl_pwd_id': 'PWD123',
        'decl_solo_parent_id': 'SP123',
    }

    with app.test_client() as client:
        resp = client.post('/employee/pds/submit', data=payload, follow_redirects=False)
        print(f"POST status: {resp.status_code}")
        if resp.status_code not in (302, 200):
            print(resp.get_data(as_text=True)[:500])
            return

    # Fetch last inserted personal_info_id
    with get_db_cursor() as cur:
        cur.execute("SELECT id, surname, first_name FROM pds_personal_information ORDER BY id DESC LIMIT 1")
        pi = cur.fetchone()
        if not pi:
            print("No personal info row found.")
            return
        pid = pi['id']
        print(f"Inserted personal_info_id={pid}, name={pi['surname']}, {pi['first_name']}")

        def dump(table):
            cur.execute(f"SELECT * FROM {table} WHERE personal_info_id = %s", (pid,))
            rows = cur.fetchall()
            print(f"{table}: {rows}")

        dump('pds_voluntary_work')
        dump('pds_training')
        dump('pds_other_information')
        dump('pds_declarations')


if __name__ == "__main__":
    run_smoke()
