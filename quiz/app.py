import os, json, random, sqlite3
from datetime import datetime
from flask import (Flask, render_template, request, session,
                   redirect, url_for, g, flash)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'one-ring-mithrandir-2026-lotr')
DB_PATH = os.environ.get('DB_PATH', '/data/quiz.db')

# ─── 60 QUESTIONS ─────────────────────────────────────────────────────────────
QUESTIONS = [
    {"id":1,  "q":"What is the name of Frodo's elvish blade that glows blue when orcs are nearby?",
     "a":"Glamdring","b":"Orcrist","c":"Sting","d":"Narsil","ans":"c","cat":"Artifacts"},
    {"id":2,  "q":"Who forged the One Ring in the fires of Mount Doom?",
     "a":"Saruman","b":"Celebrimbor","c":"Morgoth","d":"Sauron","ans":"d","cat":"Lore"},
    {"id":3,  "q":"What is the name of Gandalf's legendary horse?",
     "a":"Bill","b":"Shadowfax","c":"Hasufel","d":"Asfaloth","ans":"b","cat":"Characters"},
    {"id":4,  "q":"How many Rings of Power were given to the Dwarf lords?",
     "a":"3","b":"7","c":"9","d":"12","ans":"b","cat":"Lore"},
    {"id":5,  "q":"What is the elvish name for Rivendell?",
     "a":"Lothlórien","b":"Imladris","c":"Lindon","d":"Eregion","ans":"b","cat":"Places"},
    {"id":6,  "q":"What is Gollum's original hobbit name?",
     "a":"Déagol","b":"Trahald","c":"Sméagol","d":"Gollum","ans":"c","cat":"Characters"},
    {"id":7,  "q":"Who is the king of Rohan during the War of the Ring?",
     "a":"Éomer","b":"Théodred","c":"Théoden","d":"Helm Hammerhand","ans":"c","cat":"Characters"},
    {"id":8,  "q":"How many members make up the Fellowship of the Ring?",
     "a":"7","b":"8","c":"9","d":"12","ans":"c","cat":"Lore"},
    {"id":9,  "q":"What elvish word meaning 'friend' opens the Doors of Durin in Moria?",
     "a":"Mithril","b":"Elen","c":"Pedo","d":"Mellon","ans":"d","cat":"Lore"},
    {"id":10, "q":"What is Aragorn's name as the crowned King of Gondor?",
     "a":"Thorongil","b":"Estel","c":"Elessar","d":"Strider","ans":"c","cat":"Characters"},
    {"id":11, "q":"Who is Boromir's younger brother?",
     "a":"Denethor","b":"Faramir","c":"Imrahil","d":"Húrin","ans":"b","cat":"Characters"},
    {"id":12, "q":"Who is Legolas's father, the king of the Woodland Realm?",
     "a":"Celeborn","b":"Elrond","c":"Oropher","d":"Thranduil","ans":"d","cat":"Characters"},
    {"id":13, "q":"What type of ancient creature is Treebeard?",
     "a":"Wizard","b":"Elf","c":"Ent","d":"Huorn","ans":"c","cat":"Characters"},
    {"id":14, "q":"Who is the Lord of Lothlórien, husband of Galadriel?",
     "a":"Celebrimbor","b":"Celeborn","c":"Círdan","d":"Glorfindel","ans":"b","cat":"Characters"},
    {"id":15, "q":"Who is Saruman's spy planted inside Rohan's royal court?",
     "a":"Gollum","b":"Lurtz","c":"Gríma Wormtongue","d":"Gothmog","ans":"c","cat":"Characters"},
    {"id":16, "q":"Who gives Frodo the Phial containing the Light of Eärendil?",
     "a":"Arwen","b":"Elrond","c":"Galadriel","d":"Gandalf","ans":"c","cat":"Characters"},
    {"id":17, "q":"What is the name of Bilbo and Frodo's hobbit hole?",
     "a":"Brandy Hall","b":"Crickhollow","c":"Bag End","d":"Great Smials","ans":"c","cat":"Places"},
    {"id":18, "q":"Who ultimately destroys the One Ring in the fires of Mount Doom?",
     "a":"Frodo intentionally","b":"Sam","c":"Gandalf","d":"Gollum accidentally","ans":"d","cat":"Lore"},
    {"id":19, "q":"What is the name of Sam's faithful pony on the journey?",
     "a":"Shadowfax","b":"Hasufel","c":"Bill","d":"Asfaloth","ans":"c","cat":"Characters"},
    {"id":20, "q":"Who is Éomer's sister, the Shieldmaiden of Rohan?",
     "a":"Arwen","b":"Éowyn","c":"Goldberry","d":"Morwen","ans":"b","cat":"Characters"},
    {"id":21, "q":"In which volcanic mountain is the One Ring destroyed?",
     "a":"Caradhras","b":"Mount Doom","c":"Weathertop","d":"Zirakzigil","ans":"b","cat":"Places"},
    {"id":22, "q":"What is the name of Sauron's dark fortress in Mordor?",
     "a":"Minas Morgul","b":"Dol Guldur","c":"Barad-dûr","d":"Orthanc","ans":"c","cat":"Places"},
    {"id":23, "q":"What armor does Bilbo give Frodo that saves his life from an orc spear?",
     "a":"Dragon-scale armor","b":"Dwarven steel","c":"Mithril coat","d":"Elvish leather","ans":"c","cat":"Artifacts"},
    {"id":24, "q":"What is the Arkenstone also known as?",
     "a":"The One Ring","b":"A palantír","c":"The Heart of the Mountain","d":"A silmaril","ans":"c","cat":"Artifacts"},
    {"id":25, "q":"The sword Andúril was reforged from the shards of which broken blade?",
     "a":"Glamdring","b":"Orcrist","c":"Narsil","d":"Gurthang","ans":"c","cat":"Artifacts"},
    {"id":26, "q":"How many dwarves accompany Bilbo Baggins on the quest in The Hobbit?",
     "a":"10","b":"12","c":"13","d":"14","ans":"c","cat":"The Hobbit"},
    {"id":27, "q":"What is the name of the dragon who guards the Lonely Mountain?",
     "a":"Ancalagon","b":"Glaurung","c":"Scatha","d":"Smaug","ans":"d","cat":"The Hobbit"},
    {"id":28, "q":"Who kills Smaug the Magnificent?",
     "a":"Thorin Oakenshield","b":"Bilbo Baggins","c":"Bard the Bowman","d":"Gandalf","ans":"c","cat":"The Hobbit"},
    {"id":29, "q":"What game does Bilbo play with Gollum in the cave beneath the Misty Mountains?",
     "a":"Chess","b":"Riddles","c":"Cards","d":"Wrestling","ans":"b","cat":"The Hobbit"},
    {"id":30, "q":"Who is Thorin Oakenshield's grandfather, the former King Under the Mountain?",
     "a":"Thráin","b":"Thrór","c":"Nain","d":"Dáin","ans":"b","cat":"The Hobbit"},
    {"id":31, "q":"What is the name of the inn in Bree where the hobbits first meet Aragorn?",
     "a":"The Green Dragon","b":"The Golden Perch","c":"The Prancing Pony","d":"The Ivy Bush","ans":"c","cat":"Places"},
    {"id":32, "q":"What treacherous mountain does the Fellowship attempt to cross before Moria?",
     "a":"Mount Doom","b":"Weathertop","c":"Caradhras","d":"Zirakzigil","ans":"c","cat":"Places"},
    {"id":33, "q":"What is Gandalf's name among the elves of Middle-earth?",
     "a":"Tharkûn","b":"Olórin","c":"Mithrandir","d":"Incánus","ans":"c","cat":"Characters"},
    {"id":34, "q":"Who forged the Three Elvish Rings of Power?",
     "a":"Sauron","b":"Fëanor","c":"Celebrimbor","d":"Círdan","ans":"c","cat":"Lore"},
    {"id":35, "q":"What are the nine bearers of the Nine Rings of Men called?",
     "a":"Orcs","b":"Nazgûl","c":"Uruk-hai","d":"Trolls","ans":"b","cat":"Lore"},
    {"id":36, "q":"What is the name of Gandalf's sword, found in a troll hoard?",
     "a":"Sting","b":"Narsil","c":"Orcrist","d":"Glamdring","ans":"d","cat":"Artifacts"},
    {"id":37, "q":"What is a palantír?",
     "a":"A type of elvish bread","b":"A seeing stone","c":"A dwarvish weapon","d":"A ring of power","ans":"b","cat":"Artifacts"},
    {"id":38, "q":"What river does Arwen cross with Frodo, using its waters against the Black Riders?",
     "a":"Anduin","b":"Bruinen","c":"Sirannon","d":"Celebrant","ans":"b","cat":"Places"},
    {"id":39, "q":"Where do the Ents march to destroy after the Entmoot in Fangorn?",
     "a":"Minas Tirith","b":"Mordor","c":"Isengard","d":"Helm's Deep","ans":"c","cat":"Lore"},
    {"id":40, "q":"Whose captured starlight does the Phial of Galadriel contain?",
     "a":"Light of the Silmarils","b":"Light of Eärendil","c":"Starlight of Varda","d":"Light of the Two Trees","ans":"b","cat":"Artifacts"},
    {"id":41, "q":"How old is Bilbo when he sets off on the quest in The Hobbit?",
     "a":"40","b":"50","c":"60","d":"70","ans":"b","cat":"The Hobbit"},
    {"id":42, "q":"What lake-town near the Lonely Mountain do refugees from Dale flee to?",
     "a":"Mirkwood","b":"Rivendell","c":"Esgaroth","d":"The Iron Hills","ans":"c","cat":"The Hobbit"},
    {"id":43, "q":"What shape-changing man helps the dwarves in The Hobbit?",
     "a":"Tom Bombadil","b":"Beorn","c":"Radagast","d":"Círdan","ans":"b","cat":"The Hobbit"},
    {"id":44, "q":"What is the name of Thorin's sword, meaning 'Goblin-cleaver'?",
     "a":"Sting","b":"Orcrist","c":"Glamdring","d":"Narsil","ans":"b","cat":"The Hobbit"},
    {"id":45, "q":"How does Bilbo escape the goblin caves while wearing the ring?",
     "a":"He fights his way out","b":"He uses a spell","c":"He turns invisible","d":"He hides in barrels","ans":"c","cat":"The Hobbit"},
    {"id":46, "q":"What gold-madness afflicts Thorin near the end of The Hobbit?",
     "a":"Dragon sickness","b":"The Ring's corruption","c":"Orc poison","d":"Old age","ans":"a","cat":"The Hobbit"},
    {"id":47, "q":"What is the name of the great battle that concludes The Hobbit?",
     "a":"Battle of Helm's Deep","b":"Battle of the Pelennor","c":"Battle of Five Armies","d":"Battle of Dagorlad","ans":"c","cat":"The Hobbit"},
    {"id":48, "q":"Who is Bilbo Baggins's father?",
     "a":"Bungo Baggins","b":"Drogo Baggins","c":"Paladin Took","d":"Hamfast Gamgee","ans":"a","cat":"Characters"},
    {"id":49, "q":"What is the name of the giant spider Frodo and Sam face in her lair?",
     "a":"Ungoliant","b":"Shelob","c":"Mirkwood Queen","d":"Narya","ans":"b","cat":"Characters"},
    {"id":50, "q":"What language is used for the inscription on the One Ring?",
     "a":"Sindarin","b":"Quenya","c":"Black Speech","d":"Westron","ans":"c","cat":"Lore"},
    {"id":51, "q":"What ancient battle saw the Last Alliance of Elves and Men fight Sauron?",
     "a":"Battle of Five Armies","b":"Battle of Dagorlad","c":"Battle of the Pelennor","d":"Battle of Azanulbizar","ans":"b","cat":"Lore"},
    {"id":52, "q":"Who forged the Three, Seven and Nine Rings alongside Sauron's secret guidance?",
     "a":"Celebrimbor and the Elves of Eregion","b":"Fëanor's sons","c":"The Dwarves of Khazad-dûm","d":"Círdan's smiths","ans":"a","cat":"Lore"},
    {"id":53, "q":"What is the name of Minas Tirith's ancient name before Sauron corrupted it?",
     "a":"Minas Anor","b":"Minas Ithil","c":"Osgiliath","d":"Annúminas","ans":"a","cat":"Places"},
    {"id":54, "q":"What unique creature is Tom Bombadil?",
     "a":"An elf","b":"A wizard","c":"A Maia spirit","d":"An ancient being of unknown nature","ans":"d","cat":"Characters"},
    {"id":55, "q":"Who is the chief of the Istari, originally highest among the five wizards?",
     "a":"Gandalf","b":"Saruman","c":"Radagast","d":"Alatar","ans":"b","cat":"Characters"},
    {"id":56, "q":"What do the hobbits Merry and Pippin drink in Fangorn that makes them grow taller?",
     "a":"Ent-wine","b":"Ent-draught","c":"Fangorn sap","d":"Elvish miruvor","ans":"b","cat":"Lore"},
    {"id":57, "q":"What river forms the boundary between Rohan and Gondor?",
     "a":"Anduin","b":"Isen","c":"Entwash","d":"Mering Stream","ans":"a","cat":"Places"},
    {"id":58, "q":"How many companions does Frodo have when he leaves the Shire at the start?",
     "a":"1 (Sam only)","b":"2 (Sam and Merry)","c":"3 (Sam, Merry, Pippin)","d":"4 (Sam, Merry, Pippin, Gandalf)","ans":"c","cat":"Lore"},
    {"id":59, "q":"What is the name of the valley home of the Rohirrim's greatest fortress?",
     "a":"Fangorn","b":"Helm's Deep","c":"Edoras","d":"Dunharrow","ans":"b","cat":"Places"},
    {"id":60, "q":"How old is Bilbo when he eventually sails to the Undying Lands?",
     "a":"111","b":"120","c":"131","d":"150","ans":"c","cat":"Lore"},
]

# ─── 48 LOTR IDENTITIES + QUOTES (post-quiz rewards) ─────────────────────────
LOTR_CREDS = [
    ("frodo_baggins",        "Even small feet can change the road ahead."),
    ("samwise_gamgee",       "Hope tastes better when shared by the fire."),
    ("gandalf_mithrandir",   "Wisdom is a lantern carried into shadow."),
    ("aragorn_elessar",      "A crown is earned by service before glory."),
    ("legolas_greenleaf",    "The forest remembers every arrow and oath."),
    ("gimli_lockbearer",     "Stone and steel both sing for loyal hearts."),
    ("boromir_gondor",       "Pride unguarded is a gate left open."),
    ("merry_brandybuck",     "Courage may come in a very small laugh."),
    ("pippin_took",          "Second breakfast, first bravery, both matter."),
    ("bilbo_baggins",        "Adventure begins where comfort politely ends."),
    ("thorin_oakenshield",   "A kingdom is heavier than a chest of gold."),
    ("balin_fundinsson",     "Old halls wake when old friends return."),
    ("dwalin_fundinsson",    "Loyalty strikes harder than any axe."),
    ("fili_durin",           "Youth runs first, honor keeps pace."),
    ("kili_durin",           "A keen eye can guard a whole company."),
    ("oin_healer",           "A steady hand can mend more than wounds."),
    ("gloin_gimlifather",    "Family names are forged, not inherited."),
    ("dori_dwarves",         "Strength is best spent lifting others."),
    ("nori_dwarves",         "A clever path is still a brave one."),
    ("ori_scribe",           "Write the truth before memory turns to mist."),
    ("bifur_dwarves",        "Scars are maps that lead us home."),
    ("bofur_dwarves",        "A warm song can outlast a cold night."),
    ("bombur_dwarves",       "Good meals make good marches possible."),
    ("saruman_white",        "Power without humility speaks too loudly."),
    ("sauron_darkord",       "Every chain begins as a promise."),
    ("gollum_smeagol",       "Possession can hollow even the loudest voice."),
    ("eowyn_shieldmaiden",   "Valor answers no one who doubts your name."),
    ("faramir_ithilien",     "Mercy is the sharpest wisdom in war."),
    ("arwen_undomiel",       "Love chooses both dawn and dusk."),
    ("elrond_halfelven",     "Long years teach patience, not surrender."),
    ("galadriel_lorien",     "Light endures when hearts refuse despair."),
    ("treebeard_ent",        "Do not rush what must grow roots first."),
    ("radagast_brown",       "The wild keeps counsel for gentle ears."),
    ("eomer_rohan",          "Ride hard, but never past your honor."),
    ("theoden_king",         "Even winter kings can rise at dawn."),
    ("denethor_steward",     "Despair is a throne that burns its lord."),
    ("bard_bowman",          "One true shot can free a city."),
    ("thranduil_woodland",   "Grace and steel are kin in battle."),
    ("celeborn_lorien",      "Guard beauty fiercely, yet without greed."),
    ("haldir_marchwarden",   "Borders hold when hearts stand watch."),
    ("glorfindel_rivendell", "Bright blades are brightest in dark hours."),
    ("tom_bombadil",         "Joy is older than fear and walks singing."),
    ("beorn_skinchanger",    "Fury must serve justice, never hunger."),
    ("shelob_ungoliant",     "In deepest dark, one light still wounds."),
    ("azog_defiler",         "Cruelty crowns itself before it falls."),
    ("lurtz_urukhai",        "Blind obedience breaks before true will."),
    ("grima_wormtongue",     "Whispers can topple halls built of stone."),
    ("nazgul_ringwraith",    "Empty crowns follow the loudest command."),
]

# ─── DATABASE ─────────────────────────────────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS teams (
            id            INTEGER PRIMARY KEY,
            username      TEXT UNIQUE NOT NULL,
            password      TEXT NOT NULL,
            lotr_user     TEXT NOT NULL,
            lotr_pass     TEXT NOT NULL,
            question_ids  TEXT,
            score         INTEGER,
            completed     INTEGER DEFAULT 0,
            completed_at  TEXT
        );
        CREATE TABLE IF NOT EXISTS answers (
            team_id     INTEGER,
            question_id INTEGER,
            selected    TEXT,
            correct     INTEGER,
            PRIMARY KEY (team_id, question_id)
        );
    """)
    # Insert 48 teams if not present, then refresh LOTR identity data.
    for i, (lu, lp) in enumerate(LOTR_CREDS, 1):
        db.execute("""
            INSERT OR IGNORE INTO teams
            (id, username, password, lotr_user, lotr_pass)
            VALUES (?,?,?,?,?)
        """, (i, f"team{i:02d}", f"team{i:02d}", lu, lp))
        db.execute(
            "UPDATE teams SET lotr_user=?, lotr_pass=? WHERE id=?",
            (lu, lp, i)
        )
    db.commit()
    db.close()

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def current_team():
    if 'team_id' not in session:
        return None
    db = get_db()
    return db.execute("SELECT * FROM teams WHERE id=?", (session['team_id'],)).fetchone()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'team_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── ROUTES ───────────────────────────────────────────────────────────────────
@app.route('/', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        u = request.form.get('username','').strip()
        p = request.form.get('password','').strip()
        db = get_db()
        team = db.execute(
            "SELECT * FROM teams WHERE username=? AND password=?", (u, p)
        ).fetchone()
        if team:
            session['team_id'] = team['id']
            if team['completed']:
                return redirect(url_for('result'))
            return redirect(url_for('quiz'))
        error = "Invalid credentials. Use your assigned team username and password."
    return render_template('login.html', error=error)

@app.route('/quiz')
@login_required
def quiz():
    team = current_team()
    if team['completed']:
        return redirect(url_for('result'))

    db = get_db()
    # Assign 20 random questions if not done yet
    if not team['question_ids']:
        ids = random.sample([q['id'] for q in QUESTIONS], 20)
        db.execute("UPDATE teams SET question_ids=? WHERE id=?",
                   (json.dumps(ids), team['id']))
        db.commit()
        team = current_team()

    ids = json.loads(team['question_ids'])
    q_map = {q['id']: q for q in QUESTIONS}
    questions = [q_map[i] for i in ids]
    return render_template('quiz.html', team=team, questions=questions, total=len(questions))

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    team = current_team()
    if team['completed']:
        return redirect(url_for('result'))

    db = get_db()
    ids = json.loads(team['question_ids'])
    q_map = {q['id']: q for q in QUESTIONS}

    score = 0
    for qid in ids:
        q = q_map[qid]
        selected = request.form.get(f'q{qid}', '').lower()
        correct = 1 if selected == q['ans'] else 0
        score += correct
        db.execute("""
            INSERT OR REPLACE INTO answers (team_id, question_id, selected, correct)
            VALUES (?,?,?,?)
        """, (team['id'], qid, selected, correct))

    db.execute("""
        UPDATE teams SET score=?, completed=1, completed_at=?
        WHERE id=?
    """, (score, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), team['id']))
    db.commit()
    return redirect(url_for('result'))

@app.route('/result')
@login_required
def result():
    team = current_team()
    if not team['completed']:
        return redirect(url_for('quiz'))

    db = get_db()
    ids = json.loads(team['question_ids'])
    q_map = {q['id']: q for q in QUESTIONS}
    answers = {r['question_id']: r for r in
               db.execute("SELECT * FROM answers WHERE team_id=?", (team['id'],)).fetchall()}

    reviewed = []
    for qid in ids:
        q = q_map[qid]
        a = answers.get(qid)
        reviewed.append({
            'q': q, 'selected': a['selected'] if a else '—',
            'correct': bool(a['correct']) if a else False
        })

    # Rank
    rank_row = db.execute("""
        SELECT COUNT(*)+1 as rank FROM teams
        WHERE completed=1 AND score > ? AND id != ?
    """, (team['score'], team['id'])).fetchone()
    rank = rank_row['rank'] if rank_row else '—'
    total_completed = db.execute("SELECT COUNT(*) as c FROM teams WHERE completed=1").fetchone()['c']

    return render_template('result.html', team=team, reviewed=reviewed,
                           rank=rank, total_completed=total_completed)


@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == os.environ.get('ADMIN_PASS','admin'):
            session['admin'] = True
        else:
            return render_template('admin.html', error="Wrong password", authed=False)

    if not session.get('admin'):
        return render_template('admin.html', authed=False)

    db = get_db()
    teams = db.execute("""
        SELECT id, username, lotr_user, lotr_pass, score, completed, completed_at
        FROM teams ORDER BY id
    """).fetchall()
    stats = db.execute("""
        SELECT COUNT(*) as total,
               SUM(completed) as done,
               MAX(score) as top_score,
               AVG(CASE WHEN completed=1 THEN score END) as avg_score
        FROM teams
    """).fetchone()
    return render_template('admin.html', teams=teams, stats=stats, authed=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
