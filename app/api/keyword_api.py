"""
Keyword API endpoints for autocomplete and management
Provides smart keyword suggestions to prevent duplicates and misspellings
"""
from flask import Blueprint, request, jsonify, current_app
from app.models import Keyword, Component, keyword_component
from app import db
from sqlalchemy import func, or_
import difflib

keyword_api = Blueprint('keyword_api', __name__, url_prefix='/api/keyword')

@keyword_api.route('/search', methods=['GET'])
def search_keywords():
    """
    Search for keywords with autocomplete suggestions
    Supports fuzzy matching to find similar keywords
    """
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            # Return most frequently used keywords if no query
            popular_keywords = db.session.query(
                Keyword.id,
                Keyword.name,
                func.count(keyword_component.c.keyword_id).label('usage_count')
            ).outerjoin(
                keyword_component, Keyword.id == keyword_component.c.keyword_id
            ).group_by(
                Keyword.id, Keyword.name
            ).order_by(
                func.count(keyword_component.c.keyword_id).desc(),
                Keyword.name
            ).limit(limit).all()
            
            return jsonify({
                'keywords': [
                    {
                        'id': k.id,
                        'name': k.name,
                        'usage_count': k.usage_count,
                        'match_type': 'popular'
                    } for k in popular_keywords
                ]
            })
        
        # Direct matches (exact and starts with)
        exact_matches = Keyword.query.filter(
            Keyword.name.ilike(f'{query}%')
        ).order_by(Keyword.name).limit(limit).all()
        
        # Get all keywords for fuzzy matching if we need more results
        all_keywords = []
        if len(exact_matches) < limit:
            all_keywords = Keyword.query.all()
        
        # Prepare results
        results = []
        
        # Add exact matches first
        for keyword in exact_matches:
            usage_count = db.session.query(func.count(keyword_component.c.keyword_id)).filter(
                keyword_component.c.keyword_id == keyword.id
            ).scalar() or 0
            
            match_type = 'exact' if keyword.name.lower() == query.lower() else 'starts_with'
            
            results.append({
                'id': keyword.id,
                'name': keyword.name,
                'usage_count': usage_count,
                'match_type': match_type,
                'similarity': 1.0 if match_type == 'exact' else 0.9
            })
        
        # Add fuzzy matches if we need more results
        if len(results) < limit and all_keywords:
            fuzzy_matches = []
            query_lower = query.lower()
            
            for keyword in all_keywords:
                if keyword.id in [r['id'] for r in results]:
                    continue  # Skip already added exact matches
                
                # Calculate similarity
                similarity = difflib.SequenceMatcher(None, query_lower, keyword.name.lower()).ratio()
                
                # Only include if similarity is above threshold
                if similarity > 0.6:
                    usage_count = db.session.query(func.count(keyword_component.c.keyword_id)).filter(
                        keyword_component.c.keyword_id == keyword.id
                    ).scalar() or 0
                    
                    fuzzy_matches.append({
                        'id': keyword.id,
                        'name': keyword.name,
                        'usage_count': usage_count,
                        'match_type': 'fuzzy',
                        'similarity': similarity
                    })
            
            # Sort fuzzy matches by similarity and usage
            fuzzy_matches.sort(key=lambda x: (-x['similarity'], -x['usage_count']))
            
            # Add fuzzy matches to fill the limit
            remaining_slots = limit - len(results)
            results.extend(fuzzy_matches[:remaining_slots])
        
        return jsonify({'keywords': results})
        
    except Exception as e:
        current_app.logger.error(f"Error searching keywords: {str(e)}")
        return jsonify({'error': str(e)}), 500

@keyword_api.route('/create', methods=['POST'])
def create_keyword():
    """
    Create a new keyword or return existing one
    Prevents duplicate keywords with similar names
    """
    try:
        data = request.get_json()
        keyword_name = data.get('name', '').strip()
        
        if not keyword_name:
            return jsonify({'error': 'Keyword name is required'}), 400
        
        # Check for exact match first
        existing_keyword = Keyword.query.filter(
            func.lower(Keyword.name) == keyword_name.lower()
        ).first()
        
        if existing_keyword:
            return jsonify({
                'keyword': {
                    'id': existing_keyword.id,
                    'name': existing_keyword.name,
                    'created': False,
                    'message': 'Keyword already exists'
                }
            })
        
        # Check for very similar keywords (potential duplicates)
        all_keywords = Keyword.query.all()
        similar_keywords = []
        
        for keyword in all_keywords:
            similarity = difflib.SequenceMatcher(None, keyword_name.lower(), keyword.name.lower()).ratio()
            if similarity > 0.8:  # High similarity threshold
                similar_keywords.append({
                    'id': keyword.id,
                    'name': keyword.name,
                    'similarity': similarity
                })
        
        if similar_keywords:
            similar_keywords.sort(key=lambda x: -x['similarity'])
            return jsonify({
                'warning': 'Similar keywords found',
                'similar_keywords': similar_keywords,
                'suggested_action': 'Consider using existing keyword instead'
            }), 409
        
        # Create new keyword
        new_keyword = Keyword(name=keyword_name)
        db.session.add(new_keyword)
        db.session.commit()
        
        return jsonify({
            'keyword': {
                'id': new_keyword.id,
                'name': new_keyword.name,
                'created': True,
                'message': 'New keyword created successfully'
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating keyword: {str(e)}")
        return jsonify({'error': str(e)}), 500

@keyword_api.route('/associate', methods=['POST'])
def associate_keywords():
    """
    Associate keywords with a component
    Handles both existing and new keywords
    """
    try:
        data = request.get_json()
        component_id = data.get('component_id')
        keyword_names = data.get('keywords', [])
        
        if not component_id:
            return jsonify({'error': 'Component ID is required'}), 400
        
        component = Component.query.get_or_404(component_id)
        
        # Remove existing keyword associations
        db.session.execute(
            keyword_component.delete().where(keyword_component.c.component_id == component_id)
        )
        
        keyword_results = []
        
        for keyword_name in keyword_names:
            keyword_name = keyword_name.strip()
            if not keyword_name:
                continue
            
            # Find or create keyword
            keyword = Keyword.query.filter(
                func.lower(Keyword.name) == keyword_name.lower()
            ).first()
            
            if not keyword:
                keyword = Keyword(name=keyword_name)
                db.session.add(keyword)
                db.session.flush()  # Get the ID
                keyword_results.append({
                    'id': keyword.id,
                    'name': keyword.name,
                    'created': True
                })
            else:
                keyword_results.append({
                    'id': keyword.id,
                    'name': keyword.name,
                    'created': False
                })
            
            # Create association
            db.session.execute(
                keyword_component.insert().values(
                    component_id=component_id,
                    keyword_id=keyword.id
                )
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Associated {len(keyword_results)} keywords with component',
            'keywords': keyword_results
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error associating keywords: {str(e)}")
        return jsonify({'error': str(e)}), 500

@keyword_api.route('/stats', methods=['GET'])
def keyword_stats():
    """
    Get keyword usage statistics
    """
    try:
        # Most used keywords
        popular_keywords = db.session.query(
            Keyword.id,
            Keyword.name,
            func.count(keyword_component.c.keyword_id).label('usage_count')
        ).outerjoin(
            keyword_component, Keyword.id == keyword_component.c.keyword_id
        ).group_by(
            Keyword.id, Keyword.name
        ).order_by(
            func.count(keyword_component.c.keyword_id).desc()
        ).limit(20).all()
        
        # Total stats
        total_keywords = Keyword.query.count()
        unused_keywords = db.session.query(Keyword).outerjoin(
            keyword_component, Keyword.id == keyword_component.c.keyword_id
        ).filter(keyword_component.c.keyword_id.is_(None)).count()
        
        return jsonify({
            'total_keywords': total_keywords,
            'unused_keywords': unused_keywords,
            'popular_keywords': [
                {
                    'id': k.id,
                    'name': k.name,
                    'usage_count': k.usage_count
                } for k in popular_keywords
            ]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting keyword stats: {str(e)}")
        return jsonify({'error': str(e)}), 500