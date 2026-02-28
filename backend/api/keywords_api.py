"""
Keyword Maintenance API
Manages vocabulary database for sentiment analysis, response templates, and issue classification
"""

from flask import Blueprint, request, jsonify
from pathlib import Path
import json
from datetime import datetime

keywords_bp = Blueprint('keywords', __name__, url_prefix='/api/keywords')

# Path to keywords.json
KEYWORDS_PATH = Path(__file__).parent.parent / 'data' / 'keywords.json'


def load_keywords():
    """Load keywords from JSON file"""
    if not KEYWORDS_PATH.exists():
        return {}
    with open(KEYWORDS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_keywords(data):
    """Save keywords to JSON file"""
    KEYWORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data['metadata']['lastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(KEYWORDS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sync_to_python_config():
    """Sync JSON keywords back to Python config file"""
    keywords = load_keywords()
    config_path = Path(__file__).parent.parent / 'nlp' / 'keywords_config.py'
    
    if not config_path.exists():
        return False
    
    # Generate Python code
    python_code = '''"""
Keyword Configuration for 4-Level Priority Classification
定期審查並更新（每月 1 次推薦）

Last Updated: {timestamp}
Maintainer: {maintainer}
AUTO-GENERATED - Edit via keywords_admin.html instead
"""

'''.format(
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        maintainer=keywords.get('metadata', {}).get('maintainer', 'Sylvia Ho')
    )
    
    # Add each category
    for category in ['CRITICAL', 'STRATEGIC', 'OPERATIONAL', 'OPPORTUNITIES']:
        if category in keywords:
            cat_data = keywords[category]
            cat_var = category + '_KEYWORDS'
            python_code += f'{cat_var} = {{\n'
            for word, weight in cat_data['keywords'].items():
                python_code += f'    "{word}": {weight},\n'
            python_code += '}\n\n'
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(python_code)
    
    return True


# Routes

@keywords_bp.route('/all', methods=['GET'])
def get_all_keywords():
    """Get all keywords by category"""
    keywords = load_keywords()
    return jsonify(keywords), 200


@keywords_bp.route('/category/<category>', methods=['GET'])
def get_category(category):
    """Get keywords for specific category"""
    keywords = load_keywords()
    category_upper = category.upper()
    
    if category_upper not in keywords:
        return jsonify({'error': 'Category not found'}), 404
    
    return jsonify(keywords[category_upper]), 200


@keywords_bp.route('/search', methods=['GET'])
def search_keywords():
    """Search for keyword across all categories"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    keywords = load_keywords()
    results = {}
    
    for category, data in keywords.items():
        if category == 'metadata':
            continue
        matches = {k: v for k, v in data.get('keywords', {}).items() if query in k}
        if matches:
            results[category] = matches
    
    return jsonify(results), 200


@keywords_bp.route('/add', methods=['POST'])
def add_keyword():
    """Add new keyword to a category"""
    data = request.json
    category = data.get('category', '').upper()
    word = data.get('word', '').strip()
    weight = float(data.get('weight', 1))
    
    if not category or not word:
        return jsonify({'error': 'Category and word are required'}), 400
    
    keywords = load_keywords()
    
    if category not in keywords:
        return jsonify({'error': f'Category {category} not found'}), 404
    
    if word in keywords[category]['keywords']:
        return jsonify({'error': f'Keyword "{word}" already exists in {category}'}), 409
    
    keywords[category]['keywords'][word] = weight
    save_keywords(keywords)
    sync_to_python_config()
    
    return jsonify({'message': 'Keyword added successfully', 'category': category, 'word': word, 'weight': weight}), 201


@keywords_bp.route('/update', methods=['POST'])
def update_keyword():
    """Update existing keyword"""
    data = request.json
    category = data.get('category', '').upper()
    word = data.get('word', '').strip()
    weight = float(data.get('weight', 1))
    
    if not category or not word:
        return jsonify({'error': 'Category and word are required'}), 400
    
    keywords = load_keywords()
    
    if category not in keywords or word not in keywords[category]['keywords']:
        return jsonify({'error': f'Keyword "{word}" not found in {category}'}), 404
    
    keywords[category]['keywords'][word] = weight
    save_keywords(keywords)
    sync_to_python_config()
    
    return jsonify({'message': 'Keyword updated successfully', 'category': category, 'word': word, 'weight': weight}), 200


@keywords_bp.route('/delete', methods=['POST'])
def delete_keyword():
    """Delete keyword from category"""
    data = request.json
    category = data.get('category', '').upper()
    word = data.get('word', '').strip()
    
    if not category or not word:
        return jsonify({'error': 'Category and word are required'}), 400
    
    keywords = load_keywords()
    
    if category not in keywords or word not in keywords[category]['keywords']:
        return jsonify({'error': f'Keyword "{word}" not found in {category}'}), 404
    
    del keywords[category]['keywords'][word]
    save_keywords(keywords)
    sync_to_python_config()
    
    return jsonify({'message': 'Keyword deleted successfully', 'category': category, 'word': word}), 200


@keywords_bp.route('/move', methods=['POST'])
def move_keyword():
    """Move keyword from one category to another"""
    data = request.json
    from_category = data.get('from_category', '').upper()
    to_category = data.get('to_category', '').upper()
    word = data.get('word', '').strip()
    weight = float(data.get('weight', 1))
    
    if not from_category or not to_category or not word:
        return jsonify({'error': 'from_category, to_category, and word are required'}), 400
    
    keywords = load_keywords()
    
    if from_category not in keywords or word not in keywords[from_category]['keywords']:
        return jsonify({'error': f'Keyword "{word}" not found in {from_category}'}), 404
    
    if to_category not in keywords:
        return jsonify({'error': f'Category {to_category} not found'}), 404
    
    # Delete from old category
    del keywords[from_category]['keywords'][word]
    # Add to new category
    keywords[to_category]['keywords'][word] = weight
    
    save_keywords(keywords)
    sync_to_python_config()
    
    return jsonify({'message': f'Keyword moved from {from_category} to {to_category}', 'word': word, 'weight': weight}), 200


@keywords_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get statistics about the vocabulary"""
    keywords = load_keywords()
    stats = {}
    total_keywords = 0
    
    for category in ['CRITICAL', 'STRATEGIC', 'OPERATIONAL', 'OPPORTUNITIES']:
        if category in keywords:
            count = len(keywords[category]['keywords'])
            stats[category] = count
            total_keywords += count
    
    stats['TOTAL'] = total_keywords
    stats['lastUpdated'] = keywords.get('metadata', {}).get('lastUpdated', 'Unknown')
    
    return jsonify(stats), 200
