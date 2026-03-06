import streamlit as st

def inject_css():
    """
    Injects global enterprise-grade CSS into the Streamlit app.
    Hides default Streamlit artifacts and adds modern micro-interactions.
    """
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Global Font & Background */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Hide Streamlit Artifacts */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Layout Padding Removal */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1400px;
        }

        /* SaaS-Grade Card Styling (Tremor-inspired) */
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {
            background-color: #12141C;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"]:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 255, 170, 0.05), 0 4px 6px -2px rgba(0, 255, 170, 0.02);
            border: 1px solid rgba(0, 255, 170, 0.2);
        }

        /* Buttons (Aceternity/MagicUI inspired Glow) */
        button[kind="primary"] {
            background: linear-gradient(135deg, #00FFAA 0%, #00CC88 100%) !important;
            color: #0E1117 !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.3s ease !important;
        }
        
        button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 0 15px rgba(0, 255, 170, 0.4) !important;
            filter: brightness(1.1) !important;
        }

        button[kind="secondary"] {
            background-color: transparent !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #FAFAFA !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }

        button[kind="secondary"]:hover {
            border-color: #00FFAA !important;
            color: #00FFAA !important;
            background-color: rgba(0, 255, 170, 0.05) !important;
            transform: translateY(-1px) !important;
        }

        /* Inputs & Textareas */
        input[type="text"], textarea, div[data-baseweb="select"] {
            background-color: #1A1D27 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #FAFAFA !important;
            border-radius: 8px !important;
            transition: border-color 0.2s ease !important;
        }

        input[type="text"]:focus, textarea:focus, div[data-baseweb="select"]:focus-within {
            border-color: #00FFAA !important;
            box-shadow: 0 0 0 1px #00FFAA !important;
        }

        /* Tabs */
        button[data-baseweb="tab"] {
            background: transparent !important;
            border-bottom: 2px solid transparent !important;
        }
        
        button[aria-selected="true"] {
            border-bottom: 2px solid #00FFAA !important;
            color: #00FFAA !important;
        }
        
        /* Alerts */
        div[data-testid="stAlert"] {
            border-radius: 8px !important;
            border-left: 4px solid #00FFAA !important;
            background-color: rgba(0, 255, 170, 0.05) !important;
        }

        /* Sidebar line */
        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_header(title: str, description: str):
    """
    Standardized header component.
    """
    st.markdown(f"""
    <div style="padding-bottom: 1.5rem; border-bottom: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 2rem;">
        <h1 style="font-weight: 700; margin-bottom: 0.5rem; font-size: 2.5rem; letter-spacing: -0.025em;">
            {title}
        </h1>
        <p style="color: #A1A1AA; font-size: 1.1rem; margin: 0;">
            {description}
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str):
    """
    Renders a clean, Tremor-inspired metric card.
    """
    st.markdown(f"""
    <div style="background-color: #12141C; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 1.25rem;">
        <p style="color: #A1A1AA; font-size: 0.875rem; font-weight: 500; margin: 0 0 0.25rem 0; text-transform: uppercase; letter-spacing: 0.05em;">{label}</p>
        <p style="color: #FAFAFA; font-size: 1.875rem; font-weight: 600; margin: 0;">{value}</p>
    </div>
    """, unsafe_allow_html=True)

