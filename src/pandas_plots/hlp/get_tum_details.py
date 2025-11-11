import os
import duckdb as ddb
from IPython.display import display, HTML


def get_tum_details(z_tum_id: str, con: ddb.DuckDBPyConnection) -> None:
    """
    Prints the details of a specific tumor to the console.
    Needs con to clinical cancer data
    v2.3

    Args:
        z_tum_id (str): The ID of the tumor to retrieve details for.
        con (dbr.DuckDB): A DuckDB connection object.

    Returns:
        None
    """
    
    is_print= os.getenv("RENDERER") in ('png', 'svg')
    
    width = 145 if is_print else 2000

    if is_print:
        display(HTML("<br>"))
    
    print("pat")
    (con.sql(f"""--sql
        select
                z_pat_id,
                z_sex,
                z_age,
                z_ag05,
                Verstorben,
                Geburtsdatum,
                Geburtsdatum_Genauigkeit,
                Datum_Vitalstatus,
                Datum_Vitalstatus_Genauigkeit,
        from Patient
        join Tumor on Patient.oBDS_RKIPatientId = Tumor.z_pat_id
        where z_tum_id = '{z_tum_id}'
        order by z_tum_order
        """)
        .show(max_width=width)
    )
    print("tod")
    (con.sql(f"""--sql
        select  TodesursacheId,
                Code,
                Version,
                IsGrundleiden,
        from Todesursache tu
        join Tumor on tu.oBDS_RKIPatientId = Tumor.z_pat_id
        where z_tum_id = '{z_tum_id}'
        """)
        .show(max_width=width)
    )

    print("tum1")
    (con.sql(f"""--sql
        select  z_kkr_label,
                z_icd10,
                Diagnosedatum,
                Diagnosedatum_Genauigkeit,
                z_tum_op_count,
                z_tum_st_count,
                z_tum_sy_count,
                z_tum_fo_count,
                z_first_treatment,
                z_first_treatment_after_days,
        from Tumor
        where z_tum_id = '{z_tum_id}'
        order by z_tum_order
        """)
        .show(max_width=width)
    )

    print("tum2")
    (con.sql(f"""--sql
        select
                z_event_order,
                z_events,
                Anzahl_Tage_Diagnose_Tod,
                z_period_diag_death_day,
                DatumPSA,
                z_period_diag_psa_day,
                z_last_tum_status,
                z_class_hpv,
                z_tum_order,
        from Tumor
        where z_tum_id = '{z_tum_id}'
        order by z_tum_order
        """)
        .show(max_width=width)
    )

    print("op")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from OP
        where z_tum_id = '{z_tum_id}'
        order by z_op_order
        """)
        .project("* exclude (z_tum_id)")
        .show(max_width=width)
    )

    print("ops")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from OPS
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show(max_width=width)
    )

    print("st")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from ST
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show(max_width=width)
    )

    print("be")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from Bestrahlung
        where z_tum_id = '{z_tum_id}'
        order by z_bestr_order
        """)
        .project("* exclude (z_tum_id)")
        .show(max_width=width)
    )

    print("app")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from Applikationsart
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show(max_width=width)
    )

    print("syst")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from SYST
        where z_tum_id = '{z_tum_id}'
        order by z_syst_order
        """)
        .project("* exclude (z_tum_id)")
        .show(max_width=width)
    )

    print("fo")
    (con.sql(f"""--sql
        select *
        from Folgeereignis
        where z_tum_id = '{z_tum_id}'
        order by z_fo_order
        """)
        .project("* exclude (z_tum_id, z_kkr)")
        .show(max_width=width)
    )

    print("fo_tnm")
    (con.sql(f"""--sql
        select *
        from Folgeereignis_TNM
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id, z_kkr)")
        .show(max_width=width)
    )

    print("fo_fm")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from Folgeereignis_Fernmetastase
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show(max_width=width)
    )

    print("fo_weitere")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from Folgeereignis_WeitereKlassifikation
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show(max_width=width)
    )

    print("diag_fm")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from Diagnose_Fernmetastase
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show(max_width=width)
    )

    print("diag_weitere")
    (con.sql(f"""--sql
        select * exclude (z_kkr)
        from Diagnose_WeitereKlassifikation
        where z_tum_id = '{z_tum_id}'
        """)
        .project("* exclude (z_tum_id)")
        .show(max_width=width)
    )