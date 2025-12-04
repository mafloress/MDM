import reflex as rx
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration
CLICKUP_API_TOKEN = os.getenv('CLICKUP_API_TOKEN')
CLICKUP_LIST_ID = os.getenv('CLICKUP_LIST_ID')
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')
N8N_INVITE_WEBHOOK_URL = os.getenv('N8N_INVITE_WEBHOOK_URL')

USERS = {
    "admin": "password123"
}

class State(rx.State):
    """The app state."""
    user: str = ""
    username_input: str = ""
    password_input: str = ""
    
    # Kanban Data
    clients: list[dict] = []
    pools: dict[str, list[dict]] = {
        'INVITACIÓN': [],
        'ACEPTADO': [],
        'EN ESPERA': [],
        'VALIDACIÓN DOCTOS': [],
        'ACEPTADOS': []
    }
    
    # Modal States
    show_scrape_modal: bool = False
    show_invite_modal: bool = False
    show_add_client_modal: bool = False
    show_client_details_modal: bool = False
    
    # Form Inputs
    scrape_criteria: str = ""
    invite_category_id: str = ""
    invite_template_id: str = ""
    new_client_name: str = ""
    new_client_email: str = ""
    new_client_company: str = ""
    
    # Selected Client for Details
    selected_client: dict = {}

    @rx.var
    def is_authenticated(self) -> bool:
        return self.user != ""

    def login(self):
        if self.username_input in USERS and USERS[self.username_input] == self.password_input:
            self.user = self.username_input
            return rx.redirect("/dashboard")
        else:
            return rx.window_alert("Invalid credentials")

    def logout(self):
        self.user = ""
        return rx.redirect("/")

    def check_login(self):
        if not self.is_authenticated:
            return rx.redirect("/")

    def get_clickup_headers(self):
        if not CLICKUP_API_TOKEN:
            return None
        return {
            'Authorization': CLICKUP_API_TOKEN,
            'Content-Type': 'application/json'
        }

    def fetch_clients(self):
        if not self.is_authenticated:
            return
            
        headers = self.get_clickup_headers()
        if not headers or not CLICKUP_LIST_ID:
            # Mock Data
            self.clients = [
                {'id': '1', 'name': 'Juan Perez', 'status': {'status': 'INVITACIÓN'}, 'custom_fields': [{'name': 'Company', 'value': 'Tech Corp'}]},
                {'id': '2', 'name': 'Maria Garcia', 'status': {'status': 'ACEPTADO'}, 'custom_fields': [{'name': 'Company', 'value': 'Eventos MX'}]},
                {'id': '3', 'name': 'Carlos Lopez', 'status': {'status': 'EN ESPERA'}, 'custom_fields': [{'name': 'Company', 'value': 'Global Congress'}]},
                {'id': '4', 'name': 'Ana Silva', 'status': {'status': 'VALIDACIÓN DOCTOS'}, 'custom_fields': [{'name': 'Company', 'value': 'Travel Inc'}]},
                {'id': '5', 'name': 'Pedro Ruiz', 'status': {'status': 'ACEPTADOS'}, 'custom_fields': [{'name': 'Company', 'value': 'Mega Events'}]}
            ]
        else:
            try:
                url = f"https://api.clickup.com/api/v2/list/{CLICKUP_LIST_ID}/task"
                response = requests.get(url, headers=headers, params={'include_closed': 'true'})
                if response.status_code == 200:
                    self.clients = response.json().get('tasks', [])
                else:
                    print(f"Error fetching clients: {response.text}")
            except Exception as e:
                print(f"Error connecting to ClickUp: {e}")

        # Process Pools
        new_pools = {
            'INVITACIÓN': [],
            'ACEPTADO': [],
            'EN ESPERA': [],
            'VALIDACIÓN DOCTOS': [],
            'ACEPTADOS': []
        }
        
        for client in self.clients:
            status = client.get('status', {}).get('status', 'INVITACIÓN').upper()
            
            # Extract Company
            company = "N/A"
            for field in client.get('custom_fields', []):
                if field.get('name') == 'Company' and 'value' in field:
                    company = field['value']
                    break
            
            client_data = {
                'id': client['id'],
                'name': client['name'],
                'status': status,
                'company': company
            }
            
            # Find matching pool key
            target_pool = 'INVITACIÓN'
            for key in new_pools.keys():
                if key.upper() == status:
                    target_pool = key
                    break
            
            new_pools[target_pool].append(client_data)
            
        self.pools = new_pools

    def add_client(self):
        headers = self.get_clickup_headers()
        if headers and CLICKUP_LIST_ID:
            url = f"https://api.clickup.com/api/v2/list/{CLICKUP_LIST_ID}/task"
            payload = {
                "name": self.new_client_name,
                "description": f"Company: {self.new_client_company}\nEmail: {self.new_client_email}",
                "status": "INVITACIÓN"
            }
            try:
                requests.post(url, headers=headers, json=payload)
                self.fetch_clients()
            except Exception as e:
                print(f"Error creating task: {e}")
        
        self.show_add_client_modal = False
        self.new_client_name = ""
        self.new_client_email = ""
        self.new_client_company = ""

    def trigger_scraping(self):
        if N8N_WEBHOOK_URL:
            try:
                requests.post(N8N_WEBHOOK_URL, json={'criteria': self.scrape_criteria, 'action': 'scrape'})
            except Exception as e:
                print(f"Error triggering n8n: {e}")
        self.show_scrape_modal = False
        self.scrape_criteria = ""

    def trigger_invitations(self):
        if N8N_INVITE_WEBHOOK_URL:
            try:
                requests.post(N8N_INVITE_WEBHOOK_URL, json={'categoryId': self.invite_category_id, 'templateId': self.invite_template_id})
            except Exception as e:
                print(f"Error triggering n8n: {e}")
        self.show_invite_modal = False
        self.invite_category_id = ""
        self.invite_template_id = ""

    def open_details(self, client: dict):
        self.selected_client = client
        self.show_client_details_modal = True

    def upload_document(self):
        # Simulation
        self.show_client_details_modal = False
        return rx.window_alert("Document uploaded successfully (Simulation)")

# UI Components

def login_page():
    return rx.center(
        rx.vstack(
            rx.heading("N8N Congress Manager", size="8", margin_bottom="4"),
            rx.input(placeholder="Username", on_change=State.set_username_input),
            rx.input(placeholder="Password", type="password", on_change=State.set_password_input),
            rx.button("Login", on_click=State.login, width="100%"),
            bg="rgba(255, 255, 255, 0.1)",
            padding="2em",
            border_radius="1em",
            backdrop_filter="blur(10px)",
            border="1px solid rgba(255, 255, 255, 0.2)",
            box_shadow="0 4px 30px rgba(0, 0, 0, 0.1)",
        ),
        height="100vh",
        background="linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
    )

def kanban_card(client: dict):
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(f"#{client['id'][-4:]}", font_size="xs", color="gray.400", font_family="monospace"),
                rx.spacer(),
                rx.icon("more-vertical", size=16, color="gray")
            ),
            rx.text(client['name'], font_weight="bold", color="white"),
            rx.hstack(
                rx.icon("building", size=14, color="gray"),
                rx.text(client['company'], font_size="sm", color="gray.400"),
            ),
            align_items="start",
            width="100%"
        ),
        padding="1em",
        bg="rgba(255, 255, 255, 0.05)",
        border_radius="md",
        border="1px solid rgba(255, 255, 255, 0.1)",
        _hover={"border_color": "violet.500", "cursor": "pointer"},
        on_click=lambda: State.open_details(client)
    )

def kanban_column(name: str, clients: list[dict]):
    return rx.vstack(
        rx.hstack(
            rx.text(name, font_weight="bold", color="gray.300", font_size="sm"),
            rx.badge(len(clients), variant="solid", color_scheme="violet"),
            justify="between",
            width="100%",
            padding="0.5em"
        ),
        rx.vstack(
            rx.foreach(clients, kanban_card),
            spacing="3",
            width="100%",
        ),
        width="300px",
        min_width="300px",
        height="100%",
        padding="1em",
        bg="rgba(0, 0, 0, 0.2)",
        border_radius="xl",
        align_items="start"
    )

def dashboard():
    return rx.vstack(
        # Header
        rx.hstack(
            rx.hstack(
                rx.icon("layout-dashboard", color="violet", size=28),
                rx.heading("N8N Congress", size="6", color="white"),
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.hstack(rx.icon("bot", size=18), rx.text("Web Scraping")),
                    on_click=State.set_show_scrape_modal(True),
                    variant="surface",
                    color_scheme="gray"
                ),
                rx.button(
                    rx.hstack(rx.icon("send", size=18), rx.text("Send Invites")),
                    on_click=State.set_show_invite_modal(True),
                    color_scheme="green"
                ),
                rx.button(
                    rx.hstack(rx.icon("plus", size=18), rx.text("New Client")),
                    on_click=State.set_show_add_client_modal(True),
                    color_scheme="violet"
                ),
                rx.button(
                    rx.icon("log-out", size=18),
                    on_click=State.logout,
                    variant="ghost",
                    color_scheme="red"
                ),
                spacing="4"
            ),
            width="100%",
            padding="1.5em",
            border_bottom="1px solid rgba(255, 255, 255, 0.1)",
            bg="rgba(22, 33, 62, 0.8)",
            backdrop_filter="blur(10px)"
        ),
        # Board
        rx.hstack(
            rx.foreach(
                State.pools.entries(),
                lambda item: kanban_column(item[0], item[1])
            ),
            width="100%",
            height="calc(100vh - 80px)",
            overflow_x="auto",
            padding="2em",
            spacing="6",
            align_items="start"
        ),
        height="100vh",
        width="100vw",
        bg="#0f172a",
        on_mount=State.fetch_clients
    )

# Modals

def scrape_modal():
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Start Web Scraping"),
            rx.dialog.description("Enter search criteria for the LinkedIn scraper."),
            rx.flex(
                rx.text_area(
                    placeholder="e.g., Event Planners in Mexico...",
                    value=State.scrape_criteria,
                    on_change=State.set_scrape_criteria,
                ),
                direction="column",
                gap="3",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button("Cancel", variant="soft", color_scheme="gray"),
                ),
                rx.dialog.close(
                    rx.button("Start Robot", on_click=State.trigger_scraping),
                ),
                gap="3",
                margin_top="16px",
                justify="end",
            ),
        ),
        open=State.show_scrape_modal,
        on_open_change=State.set_show_scrape_modal,
    )

def invite_modal():
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Send Invitations"),
            rx.flex(
                rx.text("Category ID", size="2", margin_bottom="4px"),
                rx.input(value=State.invite_category_id, on_change=State.set_invite_category_id),
                rx.text("Template ID", size="2", margin_bottom="4px", margin_top="8px"),
                rx.input(value=State.invite_template_id, on_change=State.set_invite_template_id),
                direction="column",
                gap="2",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button("Cancel", variant="soft", color_scheme="gray"),
                ),
                rx.dialog.close(
                    rx.button("Send", color_scheme="green", on_click=State.trigger_invitations),
                ),
                gap="3",
                margin_top="16px",
                justify="end",
            ),
        ),
        open=State.show_invite_modal,
        on_open_change=State.set_show_invite_modal,
    )

def add_client_modal():
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Add New Client"),
            rx.flex(
                rx.text("Full Name", size="2"),
                rx.input(value=State.new_client_name, on_change=State.set_new_client_name),
                rx.text("Email", size="2"),
                rx.input(value=State.new_client_email, on_change=State.set_new_client_email),
                rx.text("Company", size="2"),
                rx.input(value=State.new_client_company, on_change=State.set_new_client_company),
                direction="column",
                gap="3",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button("Cancel", variant="soft", color_scheme="gray"),
                ),
                rx.dialog.close(
                    rx.button("Save", on_click=State.add_client),
                ),
                gap="3",
                margin_top="16px",
                justify="end",
            ),
        ),
        open=State.show_add_client_modal,
        on_open_change=State.set_show_add_client_modal,
    )

def client_details_modal():
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(State.selected_client['name']),
            rx.dialog.description(State.selected_client['company']),
            rx.separator(margin_y="1em"),
            rx.heading("Documents", size="3", margin_bottom="2"),
            rx.center(
                rx.vstack(
                    rx.icon("cloud-upload", size=40, color="gray"),
                    rx.text("Click to upload or drag and drop", color="gray"),
                    padding="2em",
                    border="2px dashed gray",
                    border_radius="md",
                    width="100%",
                    cursor="pointer",
                    on_click=State.upload_document
                )
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button("Close", variant="soft", color_scheme="gray"),
                ),
                gap="3",
                margin_top="16px",
                justify="end",
            ),
        ),
        open=State.show_client_details_modal,
        on_open_change=State.set_show_client_details_modal,
    )

def index():
    return rx.cond(
        State.is_authenticated,
        rx.fragment(
            dashboard(),
            scrape_modal(),
            invite_modal(),
            add_client_modal(),
            client_details_modal()
        ),
        login_page()
    )

app = rx.App(theme=rx.theme(appearance="dark", accent_color="violet"))
app.add_page(index, route="/")
app.add_page(dashboard, route="/dashboard", on_load=State.check_login)
