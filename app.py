import os
from functools import wraps

from flask import (
    Flask,
    flash,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# Set these environment variables in your hosting provider.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise RuntimeError("Set the SECRET_KEY environment variable.")

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError("Set the DATABASE_URL environment variable.")

# Support connection strings from providers using the older prefix.
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise RuntimeError("Set ADMIN_USERNAME and ADMIN_PASSWORD environment variables.")


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="Open")
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


BASE_STYLE = """
<style>
:root {
  --bg: #f4f7fb;
  --surface: #fff;
  --text: #172033;
  --muted: #667085;
  --primary: #4f46e5;
  --primary-dark: #4338ca;
  --border: #e4e7ec;
  --shadow: 0 12px 32px rgba(16, 24, 40, .08);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font: 16px/1.55 Arial, sans-serif;
}
.container { width: min(100% - 32px, 1000px); margin: 40px auto; }
.topbar {
  display: flex; justify-content: space-between; align-items: center;
  gap: 16px; margin-bottom: 28px;
}
.brand { font-size: 1.1rem; font-weight: 700; }
nav { display: flex; align-items: center; gap: 16px; }
a { color: var(--primary); text-decoration: none; font-weight: 600; }
a:hover { text-decoration: underline; }
.card, .ticket {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 16px; box-shadow: var(--shadow);
}
.card { padding: 28px; }
.page-title { margin: 0 0 6px; font-size: clamp(1.7rem, 4vw, 2.3rem); }
.subtitle { margin: 0 0 24px; color: var(--muted); }
label { display: block; margin: 16px 0 6px; font-weight: 600; }
input, textarea, select {
  width: 100%; padding: 12px 14px; border: 1px solid #d0d5dd;
  border-radius: 9px; background: #fff; color: var(--text); font: inherit;
}
input:focus, textarea:focus, select:focus {
  outline: 3px solid rgba(79, 70, 229, .15); border-color: var(--primary);
}
textarea { resize: vertical; }
button, .button {
  display: inline-block; border: 0; border-radius: 9px;
  padding: 11px 17px; background: var(--primary); color: white;
  font: inherit; font-weight: 700; cursor: pointer;
}
button:hover, .button:hover { background: var(--primary-dark); text-decoration: none; }
form button { margin-top: 12px; }
.error, .notice, .success { padding: 12px 14px; border-radius: 9px; }
.error, .notice { background: #fff1f0; color: #b42318; }
.success { background: #ecfdf3; color: #027a48; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 22px 0; }
.stat { padding: 18px; background: var(--surface); border: 1px solid var(--border); border-radius: 14px; }
.stat strong { display: block; font-size: 1.7rem; }
.stat span { color: var(--muted); font-size: .9rem; }
.ticket-form { display: flex; align-items: end; gap: 12px; margin-top: 16px; }
.ticket-form select { max-width: 230px; }
.ticket-form button { margin: 0; }
.badge {
  display: inline-block; padding: 4px 10px; border-radius: 999px;
  background: #eef2ff; color: #4338ca; font-size: .82rem; font-weight: 700;
}
@media (max-width: 700px) {
  .container { margin: 22px auto; }
  .topbar { align-items: flex-start; flex-direction: column; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .ticket-form { align-items: stretch; flex-direction: column; }
  .ticket-form select { max-width: none; }
}
</style>
"""


@app.route("/", methods=["GET", "POST"])
def submit_ticket():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()

        if not all((name, email, subject, description)):
            flash("Please fill in every field.")
        else:
            ticket = Ticket(
                name=name,
                email=email,
                subject=subject,
                description=description,
            )
            db.session.add(ticket)
            db.session.commit()

            return render_template_string(
                BASE_STYLE
                + """
                <main class="container">
                  <section class="card">
                    <p class="success">Your request has been received.</p>
                    <h1 class="page-title">Ticket submitted</h1>
                    <p class="subtitle">Keep this number for your records:</p>
                    <p><span class="badge">Ticket #{{ ticket.id }}</span></p>
                    <a class="button" href="{{ url_for('submit_ticket') }}">
                      Submit another ticket
                    </a>
                  </section>
                </main>
                """,
                ticket=ticket,
            )

    return render_template_string(
        BASE_STYLE
        + """
        <main class="container">
          <header class="topbar">
            <div class="brand">HelpDesk</div>
            <nav><a href="{{ url_for('login') }}">Admin login</a></nav>
          </header>

          <section class="card">
            <h1 class="page-title">How can we help?</h1>
            <p class="subtitle">
              Send us the details below and our support team will follow up.
            </p>

            {% for message in get_flashed_messages() %}
              <p class="error">{{ message }}</p>
            {% endfor %}

            <form method="post">
              <label for="name">Your name</label>
              <input id="name" name="name" maxlength="100"
                     placeholder="Jane Smith" required>

              <label for="email">Email address</label>
              <input id="email" name="email" type="email" maxlength="150"
                     placeholder="jane@example.com" required>

              <label for="subject">Subject</label>
              <input id="subject" name="subject" maxlength="200"
                     placeholder="Briefly describe the issue" required>

              <label for="description">What happened?</label>
              <textarea id="description" name="description" rows="7"
                        placeholder="Include any details that may help us."
                        required></textarea>

              <button type="submit">Submit support ticket</button>
            </form>
          </section>
        </main>
        """
    )


@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session["is_admin"] = True
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.")

    return render_template_string(
        BASE_STYLE
        + """
        <main class="container">
          <header class="topbar">
            <div class="brand">HelpDesk</div>
            <nav><a href="{{ url_for('submit_ticket') }}">User page</a></nav>
          </header>

          <section class="card">
            <h1 class="page-title">Admin login</h1>
            <p class="subtitle">Sign in to manage support tickets.</p>

            {% for message in get_flashed_messages() %}
              <p class="error">{{ message }}</p>
            {% endfor %}

            <form method="post">
              <label for="username">Username</label>
              <input id="username" name="username" autocomplete="username" required>

              <label for="password">Password</label>
              <input id="password" name="password" type="password"
                     autocomplete="current-password" required>

              <button type="submit">Log in</button>
            </form>
          </section>
        </main>
        """
    )


@app.route("/admin")
@admin_required
def dashboard():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()

    total = len(tickets)
    open_count = sum(ticket.status == "Open" for ticket in tickets)
    progress_count = sum(ticket.status == "In Progress" for ticket in tickets)
    resolved_count = sum(
        ticket.status in {"Resolved", "Closed"} for ticket in tickets
    )

    return render_template_string(
        BASE_STYLE
        + """
        <style>
          .stat { border: 0; box-shadow: 0 4px 14px rgba(16, 24, 40, .05); }
          .table-card {
            overflow: hidden; background: #fff; border: 1px solid #e5e7eb;
            border-radius: 16px; box-shadow: 0 12px 32px rgba(16, 24, 40, .08);
          }
          .table-heading {
            display: flex; justify-content: space-between; align-items: center;
            gap: 12px; padding: 20px 22px; border-bottom: 1px solid #e5e7eb;
          }
          .table-heading h2 { margin: 0; font-size: 1.1rem; }
          .table-heading span { color: #667085; font-size: .9rem; }
          .table-scroll { overflow-x: auto; }
          table { width: 100%; min-width: 1050px; border-collapse: collapse; }
          thead th {
            padding: 13px 16px; background: #f8fafc; color: #667085;
            text-align: left; font-size: .75rem; text-transform: uppercase;
            letter-spacing: .06em; border-bottom: 1px solid #e5e7eb;
          }
          tbody td {
            padding: 16px; color: #344054; font-size: .9rem;
            vertical-align: top; border-bottom: 1px solid #f0f1f3;
          }
          tbody tr:nth-child(even) { background: #fcfcfd; }
          tbody tr:hover { background: #f5f7ff; }
          .ticket-id, .date-cell { color: #667085; white-space: nowrap; }
          .ticket-id { font-weight: 700; }
          .subject-cell { min-width: 170px; color: #172033; font-weight: 700; }
          .customer-cell { min-width: 150px; }
          .email-cell { min-width: 190px; }
          .description-cell {
            min-width: 240px; max-width: 340px; color: #667085;
            white-space: pre-wrap; overflow-wrap: anywhere;
          }
          .status-pill {
            display: inline-block; padding: 5px 10px; border-radius: 999px;
            font-size: .78rem; font-weight: 700; white-space: nowrap;
          }
          .status-open { background: #fff7ed; color: #c2410c; }
          .status-progress { background: #eff6ff; color: #1d4ed8; }
          .status-resolved, .status-closed { background: #ecfdf3; color: #027a48; }
          .status-form { display: flex; align-items: center; gap: 8px; min-width: 225px; }
          .status-form select { min-width: 135px; padding: 9px 10px; font-size: .85rem; }
          .status-form button { margin: 0; padding: 9px 12px; font-size: .85rem; }
          .empty-state { padding: 52px 20px; text-align: center; }
          .empty-state h2 { margin: 0 0 8px; }
          .empty-state p { margin: 0; color: #667085; }
          @media (max-width: 700px) {
            .table-heading { align-items: flex-start; flex-direction: column; }
          }
        </style>

        <main class="container">
          <header class="topbar">
            <div class="brand">HelpDesk <span class="badge">Admin</span></div>
            <nav>
              <a href="{{ url_for('submit_ticket') }}">User page</a>
              <a href="{{ url_for('logout') }}">Log out</a>
            </nav>
          </header>

          <h1 class="page-title">Ticket dashboard</h1>
          <p class="subtitle">Review support requests and update their status.</p>

          <section class="stats">
            <div class="stat"><strong>{{ total }}</strong><span>Total tickets</span></div>
            <div class="stat"><strong>{{ open_count }}</strong><span>Open</span></div>
            <div class="stat"><strong>{{ progress_count }}</strong><span>In progress</span></div>
            <div class="stat"><strong>{{ resolved_count }}</strong><span>Resolved / closed</span></div>
          </section>

          <section class="table-card">
            <div class="table-heading">
              <h2>Support tickets</h2>
              <span>{{ total }} ticket{% if total != 1 %}s{% endif %}</span>
            </div>

            {% if tickets %}
              <div class="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Ticket</th><th>Subject</th><th>Customer</th><th>Email</th>
                      <th>Description</th><th>Submitted</th><th>Status</th><th>Update status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {% for ticket in tickets %}
                      {% set status_class = {
                        "Open": "status-open",
                        "In Progress": "status-progress",
                        "Resolved": "status-resolved",
                        "Closed": "status-closed"
                      }.get(ticket.status, "status-open") %}
                      <tr>
                        <td class="ticket-id">#{{ ticket.id }}</td>
                        <td class="subject-cell">{{ ticket.subject }}</td>
                        <td class="customer-cell">{{ ticket.name }}</td>
                        <td class="email-cell">{{ ticket.email }}</td>
                        <td class="description-cell">{{ ticket.description }}</td>
                        <td class="date-cell">{{ ticket.created_at.strftime("%b %d, %Y") }}<br>
                          {{ ticket.created_at.strftime("%I:%M %p") }}</td>
                        <td><span class="status-pill {{ status_class }}">{{ ticket.status }}</span></td>
                        <td>
                          <form class="status-form" method="post"
                                action="{{ url_for('update_ticket', ticket_id=ticket.id) }}">
                            <select name="status" aria-label="Ticket status">
                              {% for status in ["Open", "In Progress", "Resolved", "Closed"] %}
                                <option value="{{ status }}"
                                  {% if ticket.status == status %}selected{% endif %}>
                                  {{ status }}
                                </option>
                              {% endfor %}
                            </select>
                            <button type="submit">Save</button>
                          </form>
                        </td>
                      </tr>
                    {% endfor %}
                  </tbody>
                </table>
              </div>
            {% else %}
              <div class="empty-state">
                <h2>No tickets yet</h2>
                <p>Submitted support requests will appear here.</p>
              </div>
            {% endif %}
          </section>
        </main>
        """,
        tickets=tickets,
        total=total,
        open_count=open_count,
        progress_count=progress_count,
        resolved_count=resolved_count,
    )


@app.route("/admin/ticket/<int:ticket_id>/update", methods=["POST"])
@admin_required
def update_ticket(ticket_id):
    ticket = db.get_or_404(Ticket, ticket_id)
    status = request.form.get("status")
    allowed_statuses = {"Open", "In Progress", "Resolved", "Closed"}

    if status in allowed_statuses:
        ticket.status = status
        db.session.commit()

    return redirect(url_for("dashboard"))


@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("submit_ticket"))


if __name__ == "__main__":
    # For local development only. Use Gunicorn on Render.
    app.run(debug=True)