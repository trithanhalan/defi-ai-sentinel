import streamlit as st

def inject_css():
    """
    Injects dynamic global CSS with a theme selector.
    Supports Light Mode, Dark Mode, and High Contrast Accessibility.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎨 Aesthetics & Accessibility")
    theme = st.sidebar.radio(
        "Select Theme:",
        options=["Dark Mode 🌙", "Light Mode ☀️", "High Contrast 👁️"],
        index=0,
        label_visibility="collapsed"
    )

    if theme == "Dark Mode 🌙":
        css_vars = """
        :root {
            --bg-base: #0E1117;
            --bg-card: #12141C;
            --text-primary: #FAFAFA;
            --text-secondary: #A1A1AA;
            --border-subtle: rgba(255, 255, 255, 0.05);
            --border-hover: rgba(0, 255, 170, 0.2);
            --accent-glow: rgba(0, 255, 170, 0.4);
            --btn-primary-bg: linear-gradient(135deg, #00FFAA 0%, #00CC88 100%);
            --btn-primary-text: #0E1117;
            --input-bg: #1A1D27;
        }
        """
    elif theme == "Light Mode ☀️":
        css_vars = """
        :root {
            --bg-base: #FFFFFF;
            --bg-card: #F8FAFC;
            --text-primary: #0F172A;
            --text-secondary: #64748B;
            --border-subtle: #E2E8F0;
            --border-hover: #10B981;
            --accent-glow: rgba(16, 185, 129, 0.3);
            --btn-primary-bg: linear-gradient(135deg, #10B981 0%, #059669 100%);
            --btn-primary-text: #FFFFFF;
            --input-bg: #FFFFFF;
        }
        """
    else: # High Contrast
        css_vars = """
        :root {
            --bg-base: #000000;
            --bg-card: #000000;
            --text-primary: #FFFFFF;
            --text-secondary: #FFFF00;
            --border-subtle: #FFFFFF;
            --border-hover: #00FFFF;
            --accent-glow: rgba(0, 255, 255, 0.8);
            --btn-primary-bg: #FFFF00;
            --btn-primary-text: #000000;
            --input-bg: #000000;
        }
        """

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        {css_vars}

        /* Global Font & Background */
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-base) !important;
            color: var(--text-primary) !important;
        }}

        /* Hide Streamlit Artifacts */
        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        
        /* Layout Padding Removal */
        .block-container {{
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1400px;
        }}

        /* SaaS-Grade Card Styling (Tremor-inspired) */
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }}
        
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"]:hover {{
            box-shadow: 0 10px 15px -3px var(--accent-glow), 0 4px 6px -2px var(--accent-glow);
            border: 1px solid var(--border-hover);
        }}

        /* Buttons (Aceternity/MagicUI inspired Glow) */
        button[kind="primary"] {{
            background: var(--btn-primary-bg) !important;
            color: var(--btn-primary-text) !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.3s ease !important;
            border: 2px solid transparent !important;
        }}
        
        button[kind="primary"]:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 0 15px var(--accent-glow) !important;
            filter: brightness(1.1) !important;
        }}
        
        button[kind="primary"]:focus {{
            border-color: var(--text-primary) !important;
        }}

        button[kind="secondary"] {{
            background-color: transparent !important;
            border: 1px solid var(--border-subtle) !important;
            color: var(--text-primary) !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }}

        button[kind="secondary"]:hover {{
            border-color: var(--border-hover) !important;
            color: var(--border-hover) !important;
            background-color: var(--accent-glow) !important;
            transform: translateY(-1px) !important;
        }}

        /* Inputs & Textareas */
        input[type="text"], textarea, div[data-baseweb="select"] {{
            background-color: var(--input-bg) !important;
            border: 2px solid var(--border-subtle) !important;
            color: var(--text-primary) !important;
            border-radius: 8px !important;
            transition: border-color 0.2s ease !important;
        }}

        input[type="text"]:focus, textarea:focus, div[data-baseweb="select"]:focus-within {{
            border-color: var(--border-hover) !important;
            box-shadow: 0 0 0 1px var(--border-hover) !important;
        }}

        /* Tabs */
        button[data-baseweb="tab"] {{
            background: transparent !important;
            border-bottom: 2px solid transparent !important;
            color: var(--text-secondary) !important;
        }}
        
        button[aria-selected="true"] {{
            border-bottom: 2px solid var(--border-hover) !important;
            color: var(--border-hover) !important;
            font-weight: bold !important;
        }}
        
        /* Alerts */
        div[data-testid="stAlert"] {{
            border-radius: 8px !important;
            border-left: 4px solid var(--border-hover) !important;
            background-color: var(--bg-card) !important;
            color: var(--text-primary) !important;
        }}

        /* Sidebar line */
        section[data-testid="stSidebar"] {{
            border-right: 1px solid var(--border-subtle) !important;
            background-color: var(--bg-card) !important;
        }}
        
        /* Markdown text color override within stMarkdown */
        .markdown-text-container p, .markdown-text-container h1, .markdown-text-container h2, .markdown-text-container h3 {{
             color: var(--text-primary) !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_header(title: str, description: str):
    """
    Standardized header component using CSS variables for dynamic theming.
    """
    st.markdown(f"""
    <div style="padding-bottom: 1.5rem; border-bottom: 1px solid var(--border-subtle); margin-bottom: 2rem;">
        <h1 style="font-weight: 700; margin-bottom: 0.5rem; font-size: 2.5rem; letter-spacing: -0.025em; color: var(--text-primary);">
            {title}
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.1rem; margin: 0;">
            {description}
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str):
    """
    Renders a clean, Tremor-inspired metric card using CSS variables.
    """
    st.markdown(f"""
    <div style="background-color: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 1.25rem;">
        <p style="color: var(--text-secondary); font-size: 0.875rem; font-weight: 500; margin: 0 0 0.25rem 0; text-transform: uppercase; letter-spacing: 0.05em;">{label}</p>
        <p style="color: var(--text-primary); font-size: 1.875rem; font-weight: 600; margin: 0;">{value}</p>
    </div>
    """, unsafe_allow_html=True)

