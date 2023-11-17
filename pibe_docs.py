import os
import pibe
import markdown
import textwrap
from jinja2 import Environment, BaseLoader
from pathlib import Path

MARKDOWN_CSS = """
.markdown-body p {margin-bottom: 10px;}
.markdown-body ul {margin-bottom: 10px;}
.markdown-body h1 {font-size: 150%; margin-bottom: 20px;}
.markdown-body h2 {font-size: 140%; margin-bottom: 15px;}
.markdown-body h3 {font-size: 130%; margin-bottom: 15px;}
.markdown-body h4 {font-size: 110%; margin-bottom: 15px;}
.markdown-body pre {margin-top: 10px; margin-bottom: 10px;}
.markdown-body ul {
    list-style-type: circle;
        margin-left: 20px;
        padding: 0;
}

._markdown-body pre code {
    background: #f8f8f8;
}

.markdown-body code {
	color: #E74C3C;
    background: #fff;
    border: 1px solid #e1e4e5;
    font-size: 75%;
    padding: 2px;
}

.markdown-body pre {
	color: #E74C3C;
    background: #fff;
    border: 1px solid #e1e4e5;
    font-size: 75%;
    padding: 2px;
}

.markdown-body pre code {
    border: 0px ;
}

.markdown-body .admonition {
    padding: 5px;
    border: 1px solid;
}
.markdown-body .admonition p {
    margin-bottom: 0px;
}

.markdown-body .admonition .admonition-title {
    font-size: 110%;
    font-weight: bold;
}

.markdown-body .admonition.danger {
    background-color: #fca5a5;
    color: #7f1d1d;
}

.markdown-body .admonition.warning {
    background-color: #fed7aa;
    color: #9a3412;
}

.markdown-body .admonition.info {
    background-color: #60a5fa;
    color: #1e3a8a;
}

"""


DOC_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap" rel="stylesheet">

    <title>{{ title }}</title>
    <style>
        body {
            font-family: 'Montserrat', sans-serif;
        }

        {{ MARKDOWN_CSS }}
    </style>

</head>
<body class="bg-gray-50 leading-normal tracking-normal">
    <!-- Content -->
    <div class="container mx-auto mt-4 max-w-6xl">
        <div class="flex flex-row">
            <div class="flex-1 mb-10">
                <h1 class="text-4xl">{{ title }}</h1>
            </div>
            <div class="flex-0">
                <div class="flex flex-row text-4xl gap-2">
                    <div id="collapse-all" class="flex-1 border border-3 rounded-sm px-3 cursor-pointer">
                        &uarr;
                    </div>
                    <div id="expand-all" class="flex-1 border border-3 rounded-sm px-3 cursor-pointer">
                        &darr;
                    </div>

                </div>
            </div>
        </div>
        {% if description %}
        <div class="markdown-body mb-5">{{ description }}</div>
        {% endif %}
        {% for endpoint in endpoints %}
        <div class="border mb-5 p-2 ">
            <div class="flex flex-col md:flex-row ">
                <div class="flex-0 font-bold">
                    {% if endpoint.methods|length == 1 %}
                        {% if endpoint.methods[0] == "GET" %}
                            {% set method_classes = "bg-green-100 text-green-800" %}
                        {% elif endpoint.methods[0] == "POST" %}
                            {% set method_classes = "bg-blue-100 text-blue-800" %}
                        {% elif endpoint.methods[0] == "PUT" %}
                            {% set method_classes = "bg-blue-200 text-blue-500" %}
                        {% elif endpoint.methods[0] == "DELETE" %}
                            {% set method_classes = "bg-red-100 text-red-800" %}
                        {% elif endpoint.methods[0] == "HEAD" %}
                            {% set method_classes = "bg-blue-100 text-blue-800" %}
                        {% elif endpoint.methods[0] == "PATCH" %}
                            {% set method_classes = "bg-blue-100 text-blue-800" %}
                        {% elif endpoint.methods[0] == "OPTIONS" %}
                            {% set method_classes = "bg-blue-100 text-blue-800" %}
                        {% else %}
                            {% set method_classes = "bg-gray-200 text-gray-800" %}
                        {% endif %}
                    {% else %}
                        {% set method_classes = "bg-gray-200 text-gray-600" %}
                    {% endif %}
                    <div class="text-xl w-32 text-center p-2 border rounded-md {{ method_classes }}">{{ ", ".join(endpoint.methods)}}</div>
                </div>

                <div class="flex-1 py-2 px-5"><code class="font-bold">{{ endpoint.pattern|escape }}</code> <em>{{ endpoint.title }}</em></div>
                <div class="flex-0 py-2 flex flex-row text-4xl gap-2">
                    <div id="expand-{{ loop.index }}" class="flex-1 border border-3 rounded-sm px-3 cursor-pointer">
                        &darr;
                    </div>
                    <div id="collapse-{{loop.index}}" class="flex-1 border border-3 rounded-sm px-3 cursor-pointer hidden">
                        &uarr;
                    </div>
                </div>
            </div>
            <div id="endpoint-documentation-{{loop.index}}" class="markdown-body endpoint-documentation mt-5 mx-1 hidden">{{ endpoint.html_doc }}</div>
        </div>
        {% endfor %}
    </div>
    <script>
    {% for i in range(endpoints|length) %}
    document.getElementById("expand-{{ i+ 1 }}").addEventListener("click", (event) => {
        document.getElementById("expand-{{ i + 1 }}").classList.add("hidden");
        document.getElementById("collapse-{{ i + 1 }}").classList.remove("hidden");
        document.getElementById("endpoint-documentation-{{ i + 1 }}").classList.remove("hidden");
    });
    document.getElementById("collapse-{{ i+ 1 }}").addEventListener("click", (event) => {
        document.getElementById("expand-{{ i + 1 }}").classList.remove("hidden");
        document.getElementById("collapse-{{ i + 1 }}").classList.add("hidden");
        document.getElementById("endpoint-documentation-{{ i + 1 }}").classList.add("hidden");
    });
    {% endfor %}

    document.getElementById("expand-all").addEventListener("click", (event) => {
        {% for i in range(endpoints|length) %}
        document.getElementById("expand-{{ i + 1 }}").classList.add("hidden");
        document.getElementById("collapse-{{ i + 1 }}").classList.remove("hidden");
        document.getElementById("endpoint-documentation-{{ i + 1 }}").classList.remove("hidden");
        {% endfor %}
    });

    document.getElementById("collapse-all").addEventListener("click", (event) => {
        {% for i in range(endpoints|length) %}
        document.getElementById("expand-{{ i + 1 }}").classList.remove("hidden");
        document.getElementById("collapse-{{ i + 1 }}").classList.add("hidden");
        document.getElementById("endpoint-documentation-{{ i + 1 }}").classList.add("hidden");
        {% endfor %}
    });
    </script>
</body>
</html>
"""



def generate_documentation(router, **kwargs):
    endpoints = []
    for (regex, resource, methods, pattern, opts) in router:

        mrkdn_txt = ((textwrap.dedent(resource.__doc__) if resource.__doc__ else None)
                      or opts.get("doc")
                      or "*No documentation*")
        endpoints.append({
            "pattern": pattern,
            "methods": methods,
            "title": opts.get("title") or resource.__name__.replace("_", " ").capitalize(),
            "html_doc": markdown.markdown(mrkdn_txt, extensions=['admonition', 'fenced_code'])
        })
    title = kwargs.get("title") or "Documentation"
    description = (markdown.markdown(kwargs.get("description"))
                   if kwargs.get("description")
                   else None)
    template = Environment(loader=BaseLoader()).from_string(DOC_TEMPLATE).render(
        endpoints=endpoints,
        title=title,
        description=description,
        MARKDOWN_CSS=MARKDOWN_CSS
    )

    basepath = Path(kwargs.get("basepath", "docs_html"))

    if not basepath.exists():
        os.makedirs(basepath.absolute(), exist_ok=True)

    if not basepath.is_dir():
        raise ValueError("basepath is not a directory")

    for _extra_filepath in kwargs.get("extra", []):
        fp = Path(_extra_filepath)
        if not fp.exists():
            raise ValueError(f"file {fp} does not exist")
        with open(fp, 'r') as f:
            html = Environment(loader=BaseLoader()).from_string(EXTRA_TEMPLATE).render(
                content=markdown.markdown(f.read(), extensions=['admonition', 'fenced_code']),
                MARKDOWN_CSS=MARKDOWN_CSS
            )

        with open(basepath / f"{fp.stem}.html", 'w') as f:
            f.write(html)

    filepath = basepath / kwargs.get("filename", "index.html")

    with open(filepath, "w") as f:
        # Writing data to file
        f.write(template)
