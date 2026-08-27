import requests
from urllib.parse import urljoin

base_url = "http://localhost:80/"

top_level = ["admin", "users", "register", "login", "api", "products", "orders", 
             "payments", "invoices", "files", "images", "videos", "settings",
             "projects", "reset-password"]


subpaths = [
    # Genéricos / CRUD
    "list", "create", "new", "edit", "update", "delete", "remove",
    "view", "show", "detail", "details", "get", "set", "add",
    "save", "submit", "search", "filter", "export", "import",
    "upload", "download", "print", "preview",

    # Autenticação / Usuários
    "login", "logout", "signin", "signup", "register", "auth",
    "password", "reset-password", "forgot-password", "profile",
    "account", "settings", "preferences", "roles", "permissions",
    "sessions", "token", "refresh", "verify", "activate", "deactivate",

    # API
    "v1", "v2", "v3", "api", "rest", "graphql", "json", "xml",
    "docs", "swagger", "openapi", "schema", "health", "status",
    "version", "info", "config", "metrics", "logs", "debug",

    # Administração
    "admin", "dashboard", "panel", "manage", "management",
    "configuration", "config", "setup", "install", "update",
    "backup", "restore", "logs", "reports", "statistics", "stats",
    "users", "groups", "permissions", "acl", "audit", "monitor",

    # Conteúdo / Mídia
    "files", "images", "uploads", "media", "assets", "static",
    "public", "private", "thumbnails", "avatar", "cover", "photo",
    "video", "audio", "document", "docs", "archive", "download",

    # E-commerce
    "products", "items", "orders", "cart", "checkout", "payment",
    "payments", "invoice", "invoices", "billing", "shipping",
    "categories", "tags", "reviews", "ratings", "coupons", "discounts",

    # Comum em aplicações
    "home", "index", "main", "about", "contact", "help", "faq",
    "support", "terms", "privacy", "legal", "sitemap", "robots",
    "feed", "rss", "atom", "blog", "news", "articles", "posts",
    "comments", "messages", "notifications", "alerts", "events",
    "calendar", "tasks", "projects", "clients", "partners", "team",

    # Arquivos sensíveis / administrativos (para testes autorizados)
    "backup", "db", "database", "dump", "sql", "conf", "config",
    "env", "ini", "log", "logs", "tmp", "temp", "cache", "vendor",
    "node_modules", "storage", "app", "src", "test", "tests",
    "debug", "trace", "error", "errors", "phpinfo", "server-status",
    "server-info", "console", "shell", "cmd", "exec",
]


possible_routes_api = []


def concatenate_routes(top_level, subpaths):
    for routes in top_level:
        less_url = urljoin(base_url, routes)
        possible_routes_api.append(less_url)
        for sub in subpaths:
            full_url = urljoin(base_url, f"{routes}/{sub}")
            possible_routes_api.append(full_url)



def save_output():
    with open("saida.txt", "w", encoding="utf-8") as arquivo:
                for linha in possible_routes_api:
                    print(linha, file=arquivo)

def requests_send():
     requests.post()

def main():
      concatenate_routes(top_level, subpaths)