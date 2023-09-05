from datetime import datetime
from flask import flash, redirect, render_template, request, session, url_for
from helpers import dict_factory
import sqlite3

titles = ["Engineer", "Team Lead", "Operator", "Quality inspector"]

defects = [
    ("DF01", "Filling is missing"),
    ("DF02", "Overfill"),
    ("DC01", "Coating is missing"),
    ("DC02", "Coating is leaking"),
    ("DT01", "Topping is missing"),
    ("DT02", "Topping is misplaced"),
]


def analysis():
    param = request.args.get("parameter")
    defect = request.args.get("defect")
    process = request.args.get("process")

    values = []
    results = []

    parameter = ""

    if param == "line":
        parameter = "Line"

        with sqlite3.connect("bonbons.db") as con:
            con.row_factory = dict_factory
            db = con.cursor()
            res = db.execute(
                "SELECT COUNT(*) FROM processes WHERE batch IN (SELECT id FROM batches WHERE quality IS NOT NULL) AND process = ?",
                (process,),
            )
            runs = res.fetchone()["COUNT(*)"]

            for l in range(10):
                line = l + 1
                res = db.execute(
                    "SELECT COUNT(*) FROM inspections WHERE bonbon IN (SELECT id FROM bonbons WHERE line = ? AND batch IN (SELECT id FROM batches WHERE quality IS NOT NULL)) AND defect = ?",
                    (line, defect),
                )
                bonbons_defected = res.fetchone()["COUNT(*)"]

                result = {}

                result["value"] = line
                result["processed"] = runs
                result["defected"] = bonbons_defected

                if result["processed"] != 0:
                    result["ratio"] = "{:.1%}".format(
                        result["defected"] / result["processed"]
                    )
                else:
                    result["ratio"] = "n/a"

                results.append(result)

    elif param in ("temp", "type"):
        if param == "temp":
            parameter = "Temperature"
        if param == "type":
            parameter = "Type"

        with sqlite3.connect("bonbons.db") as con:
            con.row_factory = dict_factory
            db = con.cursor()

            res = db.execute(
                f"SELECT DISTINCT {param} FROM processes WHERE process = '{process}' AND batch IN (SELECT id FROM batches WHERE Quality IS NOT NULL) ORDER BY {param}"
            )
            vars = list(res.fetchall())
            for var in vars:
                values.append(var[param])

            for value in values:
                res = db.execute(
                    f"SELECT batch, box FROM processes WHERE {param} = '{value}' AND process = '{process}' AND batch IN (SELECT id FROM batches WHERE quality IS NOT NULL)"
                )
                boxlist = list(res.fetchall())

                boxes = []
                for box in boxlist:
                    boxes.append((box["batch"], box["box"]))

                bonbons_all = []

                for boxx in boxes:
                    res = db.execute(
                        "SELECT id FROM bonbons WHERE batch = ? AND box = ?",
                        (boxx[0], boxx[1]),
                    )
                    bonbons_a = list(res.fetchall())

                    for bonbon in bonbons_a:
                        bonbons_all.append(bonbon["id"])

                placeholders = ",".join(["?" for _ in bonbons_all])
                query = f"SELECT COUNT(*) FROM inspections WHERE bonbon IN ({placeholders}) AND defect = ?"
                res = db.execute(query, (*bonbons_all, defect))
                bonbons_defected = res.fetchone()["COUNT(*)"]

                # bonbons_defected = 0
                # for bonbon in bonbons_all:
                #     res = db.execute("SELECT * FROM inspections WHERE bonbon = ? AND defect = ?", (bonbon, defect))
                #     if res.fetchone():
                #         bonbons_defected = bonbons_defected + 1


                result = {}

                result["value"] = value
                result["processed"] = len(bonbons_all)
                result["defected"] = bonbons_defected

                if result["processed"] != 0:
                    result["ratio"] = "{:.1%}".format(
                        result["defected"] / result["processed"]
                    )
                else:
                    result["ratio"] = "n/a"

                results.append(result)

    return render_template(
        "analysis.html",
        parameter=parameter,
        defect=defect,
        proc=process,
        results=results,
    )


def batch_details(batchname):
    batchname = batchname.upper()

    with sqlite3.connect("bonbons.db") as con:
        con.row_factory = dict_factory
        db = con.cursor()

        res = db.execute("SELECT id, comment FROM batches WHERE name = ?", (batchname,))
        batch = res.fetchone()
        batchid = batch["id"]
        comment = batch["comment"]

        res = db.execute(
            "SELECT * FROM processes WHERE batch = ? ORDER BY box", (batchid,)
        )
        boxdata = list(res.fetchall())

        Filling = []
        Coating = []
        Topping = []

        for box in boxdata:
            if box["process"] == "Filling":
                Filling.append(box)
            elif box["process"] == "Coating":
                Coating.append(box)
            elif box["process"] == "Topping":
                Topping.append(box)

        areas = [Filling, Coating, Topping]

        res = db.execute("SELECT * FROM users")
        users = list(res.fetchall())

        workers = {}

        for user in users:
            workers[user["id"]] = user["username"]

    return render_template(
        "batch-details.html",
        comment=comment,
        batchname=batchname,
        areas=areas,
        workers=workers,
    )


def batch_new():
    with sqlite3.connect("bonbons.db") as con:
        con.row_factory = dict_factory
        db = con.cursor()
        res = db.execute("SELECT name FROM batches")
        names = list(res.fetchall())

        batches = []

        for name in names:
            batches.append(name["name"].upper())

    return render_template("batch.html", batches=batches)


def batch_overview():
    with sqlite3.connect("bonbons.db") as con:
        con.row_factory = dict_factory
        db = con.cursor()

        res = db.execute("SELECT id, username FROM users WHERE area = 'Filling'")
        users = list(res.fetchall())

        creators = {}
        for user in users:
            creators[user["id"]] = user["username"]

        res = db.execute("SELECT * FROM batches ORDER BY name")
        batches = list(res.fetchall())

    return render_template("overview.html", batches=batches, creators=creators)


def batch_saved():
    batchname = request.form.get("batchname").upper()
    comment = request.form.get("comment")
    created = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    with sqlite3.connect("bonbons.db") as con:
        con.row_factory = dict_factory
        db = con.cursor()
        res = db.execute(
            "SELECT firstname, lastname, username FROM users WHERE id = ?",
            (session["user_id"],),
        )
        names = res.fetchone()

        db.execute(
            "INSERT INTO batches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                None,
                batchname,
                comment,
                session["user_id"],
                created,
                None,
                None,
                None,
                None,
            ),
        )
        con.commit()

        res = db.execute("SELECT id FROM batches WHERE name = ?", (batchname,))
        batchid = res.fetchone()["id"]

        for b in range(5):
            box = b + 1
            for l in range(10):
                line = l + 1
                db.execute(
                    "INSERT INTO bonbons VALUES (?, ?, ?, ?)",
                    (None, batchid, box, line),
                )
        con.commit()

    message = (
        "Batch "
        + batchname
        + " was succesfully created by "
        + names["firstname"]
        + " "
        + names["lastname"]
        + " (as "
        + names["username"]
        + ") at "
        + created
        + "."
    )

    flash(message)
    return redirect("/home")


def inspection_new():
    batchname = request.args.get("batchname").upper()

    with sqlite3.connect("bonbons.db") as con:
        con.row_factory = dict_factory
        db = con.cursor()
        res = db.execute(
            "SELECT * FROM bonbons WHERE batch = (SELECT id FROM batches WHERE name = ?)",
            (batchname,),
        )
        items = list(res.fetchall())

        res = db.execute(
            "SELECT * FROM batches WHERE name = ?",
            (batchname,),
        )
        done = res.fetchone()["quality"]

    bonbons = {}

    for item in items:
        position = str(item["box"]) + "-" + str(item["line"])
        bonbons[position] = item["id"]

    return render_template(
        "inspection.html",
        batchname=batchname,
        done=done,
        bonbons=bonbons,
        defects=defects,
    )


def inspection_saved():
    batchname = request.form.get("batchname").upper()
    action = request.form.get("action")
    inspected = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    with sqlite3.connect("bonbons.db") as con:
        con.row_factory = dict_factory
        db = con.cursor()
        db.execute(
            "UPDATE batches SET 'Quality' = ? WHERE name = ?", (inspected, batchname)
        )

        if action == "Append":
            db.execute(
                "DELETE FROM inspections WHERE bonbon IN (SELECT id FROM bonbons WHERE batch = (SELECT id FROM batches WHERE name = ?)) AND defect = 'None'",
                (batchname,),
            )

        if action == "Overwrite":
            db.execute(
                "DELETE FROM inspections WHERE bonbon IN (SELECT id FROM bonbons WHERE batch = (SELECT id FROM batches WHERE name = ?))",
                (batchname,),
            )

        con.commit()

    for i in range(5):
        for j in range(10):
            box = i + 1
            line = j + 1

            with sqlite3.connect("bonbons.db") as con:
                con.row_factory = dict_factory
                db = con.cursor()
                res = db.execute(
                    "SELECT id FROM bonbons WHERE batch = (SELECT id FROM batches WHERE name = ?) AND box = ? AND line = ?",
                    (batchname, box, line),
                )
                name = str(res.fetchone()["id"])

                defects = request.form.getlist(name)

                previous = list(
                    db.execute(
                        "SELECT defect FROM inspections WHERE bonbon = ?", (name,)
                    ).fetchall()
                )
                prev = []
                for item in previous:
                    prev.append(item["defect"])

                if len(defects) > 0:
                    for defect in defects:
                        if defect not in prev:
                            db.execute(
                                "INSERT INTO inspections VALUES ((SELECT id FROM bonbons WHERE batch = (SELECT id FROM batches WHERE name = ?) AND box = ? AND line = ?), ?, ?, ?)",
                                (
                                    batchname,
                                    box,
                                    line,
                                    defect,
                                    session["user_id"],
                                    inspected,
                                ),
                            )
                elif not previous:
                    db.execute(
                        "INSERT INTO inspections VALUES ((SELECT id FROM bonbons WHERE batch = (SELECT id FROM batches WHERE name = ?) AND box = ? AND line = ?), ?, ?, ?)",
                        (
                            batchname,
                            box,
                            line,
                            "None",
                            session["user_id"],
                            inspected,
                        ),
                    )
                con.commit()

    return redirect(url_for("view_inspection", batchname=batchname))


def inspection_view(batchname):
    batchname = batchname.upper()

    with sqlite3.connect("bonbons.db") as con:
        con.row_factory = dict_factory
        db = con.cursor()

        res = db.execute(
            "SELECT * FROM bonbons WHERE batch = (SELECT id FROM batches WHERE name = ? ORDER BY id)",
            (batchname,),
        )
        bonbons = list(res.fetchall())

        res = db.execute(
            "SELECT * FROM inspections WHERE bonbon IN (SELECT id FROM bonbons WHERE batch = (SELECT id FROM batches WHERE name = ?) ORDER BY id) ORDER BY datetime DESC",
            (batchname,),
        )
        inspects = list(res.fetchall())
        latest = inspects[0]["datetime"]

    defects = {}

    for inspect in inspects:
        for bonbon in bonbons:
            if bonbon["id"] == inspect["bonbon"]:
                position = str(bonbon["box"]) + "-" + str(bonbon["line"])
                if position not in defects:
                    defects[position] = []
                defects[position].append(inspect["defect"])

    return render_template(
        "inspection-saved.html",
        batchname=batchname,
        defects=defects,
        bonbons=bonbons,
        latest=latest,
    )


def process_new():
    process = request.args.get("process")
    batchname = request.args.get("batchname")

    with sqlite3.connect("bonbons.db") as con:
        con.row_factory = dict_factory
        db = con.cursor()
        res = db.execute("SELECT comment FROM batches WHERE name = ?", (batchname,))
        comment = res.fetchone()["comment"]

    return render_template(
        "process.html", batchname=batchname, process=process, comment=comment
    )


def process_saved():
    batchname = request.form.get("batchname")
    process = request.form.get("process")
    processed = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    with sqlite3.connect("bonbons.db") as con:
        con.row_factory = dict_factory
        db = con.cursor()

        res = db.execute("SELECT id FROM batches WHERE name = ?", (batchname,))
        batchid = res.fetchone()["id"]

        for i in range(5):
            box = i + 1
            query = "temp-" + str(box)
            temp = request.form.get(query)
            query = "type-" + str(box)
            type = request.form.get(query)
            comment = request.form.get("comment")

            db.execute(
                "INSERT INTO processes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    batchid,
                    box,
                    process,
                    temp,
                    type,
                    comment,
                    session["user_id"],
                    processed,
                ),
            )
        con.commit()

        query = "UPDATE batches SET " + process + " = ? WHERE name = ?"
        db.execute(query, (processed, batchname))
        con.commit()

    return redirect(url_for("details", batchname=batchname))
