from flask import Flask, render_template_string, request, jsonify
import os
import re
import json

app = Flask(__name__)
highlighted_sets = []

# Word class to store each word, its position, and timestamp
class Word:
    def __init__(self, text, index, timestamp):
        self.text = text
        self.index = index
        self.timestamp = timestamp

# Function to read the text file and extract the words and timestamps
def extract_words(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    skip_header_lines = 6  
    lines = content.split('\n')
    relevant_text = '\n'.join(lines[skip_header_lines:])
    first_word_match = re.match(r'^\s*([^<\s]+)', relevant_text)
    first_word_timestamp = "00:00:00.000"
    if first_word_match:
        first_word = first_word_match.group(1).strip().replace(' ', '')
    else:
        first_word = ''
    matches = re.findall(r'<(\d{2}:\d{2}:\d{2}\.\d{3})><c>(.*?)</c>', relevant_text)
    
    word_objects = []
    if first_word:
        word_objects.append(Word(text=first_word, index=0, timestamp=first_word_timestamp))
    for i, (timestamp, word) in enumerate(matches):
        word = word.replace(' ', '')
        word_objects.append(Word(text=word, index=i + 1, timestamp=timestamp))
    return word_objects

@app.route('/')
def display_text():
    file_path = os.path.join(os.path.dirname(__file__), 'captions.txt')
    word_objects = extract_words(file_path)
    total_seconds = 15
    window_seconds = 8
    screen_width = 2560 # screen pixels
    pixels_per_second = screen_width / window_seconds
    timeline_width = total_seconds * pixels_per_second

    def timestamp_to_seconds(timestamp):
        try:
            match = re.match(r'^(\d{2}):(\d{2}):(\d{2})\.(\d{3})$', timestamp)
            if not match:
                raise ValueError("Timestamp format is incorrect")
            
            h, m, s, ms = match.groups()
            h = float(h)
            m = float(m)
            seconds = float(s)
            milliseconds = float(ms)
            total_seconds = h * 3600 + m * 60 + seconds + milliseconds / 1000
            return total_seconds
        except ValueError as e:
            print(f'Error processing timestamp: {e}')
            return 0

    words_with_positions = [
        {
            'text': word.text,
            'position': timestamp_to_seconds(word.timestamp) * pixels_per_second,
            'index': word.index,
            'timestamp': word.timestamp
        }
        for word in word_objects
    ]
    
    # HTML template with inline CSS and JavaScript, modify as needed
    html_template = f'''
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>Timeline with Words</title>
        <style>
          body {{
            margin: 0;
            padding: 0;
            overflow-x: scroll;
            font-size: 24px;
          }}
          .timeline {{
            position: relative;
            width: {timeline_width}px;
            height: 100vh;
            background-color: white;
          }}
          .line {{
            position: absolute;
            top: 50%;
            left: 0;
            width: 100%;
            height: 2px;
            background-color: black;
          }}
          .tick {{
            position: absolute;
            top: 45%;
            font-size: 24px;
            font-weight: bold;
            transform: translateY(-50%);
          }}
          .word {{
            position: absolute;
            font-size: 24px;
            font-weight: bold;
            transform: translateY(-50%);
            top: 25%;
            white-space: nowrap;
            cursor: pointer;
          }}
        </style>
      </head>
      <body>
        <div class="timeline">
          <div class="line"></div>
          {"".join(f'<div class="tick" style="left: {i * pixels_per_second}px;">{i}s</div>' for i in range(total_seconds + 1))}
          {"".join(f'<div class="word" data-index="{word["index"]}" data-timestamp="{word["timestamp"]}" style="left: {word["position"]}px;">{word["text"]}</div>' for word in words_with_positions)}
        </div>
        <script>
          let firstClick = null;
          document.querySelectorAll('.word').forEach(word => {{
            word.addEventListener('click', function() {{
              if (!firstClick) {{
                firstClick = this;
                this.style.backgroundColor = getRandomColor();
              }} else {{
                let secondClick = this;
                highlightBetween(firstClick, secondClick);
                firstClick = null;
              }}
            }});
          }});

          function highlightBetween(first, second) {{
            let start = Math.min(first.dataset.index, second.dataset.index);
            let end = Math.max(first.dataset.index, second.dataset.index);
            let endTimestamp = getEndTimestamp(end);

            let randomColor = getRandomColor();

            document.querySelectorAll('.word').forEach(word => {{
              let index = parseInt(word.dataset.index);
              if (index >= start && index <= end) {{
                word.style.backgroundColor = randomColor;
              }}
            }});

            fetch('/save_highlight', {{
              method: 'POST',
              headers: {{
                'Content-Type': 'application/json'
              }},
              body: JSON.stringify({{
                start: first.innerText,
                start_timestamp: first.dataset.timestamp,
                end: second.innerText,
                end_timestamp: endTimestamp
              }})
            }});
          }}

          function getEndTimestamp(index) {{
            let words = document.querySelectorAll('.word');
            if (index + 1 < words.length) {{
              return words[index + 1].dataset.timestamp;
            }}
            return words[index].dataset.timestamp;
          }}

          function getRandomColor() {{
            let letters = '0123456789ABCDEF';
            let color = '#';
            for (let i = 0; i < 6; i++) {{
              color += letters[Math.floor(Math.random() * 16)];
            }}
            return color;
          }}

          document.addEventListener('keydown', function(event) {{
            if (event.key === 's') {{
              fetch('/save_highlighted_sets', {{
                method: 'POST',
                headers: {{
                  'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{}})
              }});
            }}
          }});
        </script>
      </body>
    </html>
    '''
    
    return render_template_string(html_template)

# Endpoint to save individual highlights
@app.route('/save_highlight', methods=['POST'])
def save_highlight():
    data = request.json
    highlighted_sets.append({
        'start': data['start'],
        'start_timestamp': data['start_timestamp'],
        'end': data['end'],
        'end_timestamp': data['end_timestamp']
    })
    return jsonify({"status": "success"})

# Endpoint to save all highlighted sets
@app.route('/save_highlighted_sets', methods=['POST'])
def save_highlighted_sets():
    save_path = os.path.join(os.path.dirname(__file__), 'highlighted_words.json')
    with open(save_path, 'w') as f:
        json.dump(highlighted_sets, f, indent=4)
    return jsonify({"status": "success", "message": "Highlighted words saved to JSON file."})

if __name__ == '__main__':
    app.run(debug=True)
