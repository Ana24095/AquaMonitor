import streamlit as st
import base64

def create_logo():
    """Create SVG logo for Aqua Nova"""
    
    # SVG content for Aqua Nova logo
    svg_code = '''
    <svg width="150" height="150" viewBox="0 0 150 150" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="75" cy="75" r="55" stroke="white" stroke-width="4" stroke-dasharray="10 5"/>
      <path d="M39.7773 105V91.6836H30.0117V105H26V77.5586H30.0117V88.0977H39.7773V77.5586H43.7891V105H39.7773Z" fill="white"/>
      <path d="M56.6172 77.5586L61.7812 95.5547L66.9805 77.5586H71.7188L63.4688 105H60.0938L51.8789 77.5586H56.6172Z" fill="white"/>
      <path d="M81.7188 81.1445H73.7969V77.5586H93.875V81.1445H85.9531V105H81.7188V81.1445Z" fill="white"/>
      <path d="M95.0664 77.5586H99.0781V105H95.0664V77.5586Z" fill="white"/>
      <path d="M108.613 77.5586L113.379 85.4414L118.18 77.5586H122.918L115.922 88.6602L123.129 105H118.32L113.379 93.0352L108.402 105H103.664L110.906 88.6602L103.91 77.5586H108.613Z" fill="white"/>
    </svg>
    '''
    
    # Encode SVG to base64
    b64 = base64.b64encode(svg_code.encode('utf-8')).decode('utf-8')
    
    # Return the full HTML image tag
    return f'<img src="data:image/svg+xml;base64,{b64}" width="150" height="150">'

def save_logo():
    """Save the logo as PNG"""
    # This is a placeholder - in a real app this would convert SVG to PNG
    # For now, we'll just use the SVG directly via st.markdown
    with open('logo.png', 'wb') as f:
        svg_code = '''
        <svg width="150" height="150" viewBox="0 0 150 150" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="75" cy="75" r="55" stroke="white" stroke-width="4" stroke-dasharray="10 5"/>
          <path d="M39.7773 105V91.6836H30.0117V105H26V77.5586H30.0117V88.0977H39.7773V77.5586H43.7891V105H39.7773Z" fill="white"/>
          <path d="M56.6172 77.5586L61.7812 95.5547L66.9805 77.5586H71.7188L63.4688 105H60.0938L51.8789 77.5586H56.6172Z" fill="white"/>
          <path d="M81.7188 81.1445H73.7969V77.5586H93.875V81.1445H85.9531V105H81.7188V81.1445Z" fill="white"/>
          <path d="M95.0664 77.5586H99.0781V105H95.0664V77.5586Z" fill="white"/>
          <path d="M108.613 77.5586L113.379 85.4414L118.18 77.5586H122.918L115.922 88.6602L123.129 105H118.32L113.379 93.0352L108.402 105H103.664L110.906 88.6602L103.91 77.5586H108.613Z" fill="white"/>
        </svg>
        '''
        f.write(svg_code.encode('utf-8'))
        
if __name__ == "__main__":
    save_logo()