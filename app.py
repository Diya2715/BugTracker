from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# temporary storage
bugs = []
bug_id_counter = 1
comments = []
comment_id_counter = 1
users = ['Admin 1', 'Admin 2', 'Admin 3']

@app.route('/')
def dashboard():
    total = len(bugs)
    #Count total bugs
    open_count = 0
    for bug in bugs:
        if bug['status'] == 'open':
            open_count +=1
            
    # Count progress bugs
    progress_count = 0
    for bug in bugs:
        if bug['status'] == 'progress':
            progress_count += 1
            
    # Count closed bugs
    closed_count = 0
    for bug in bugs:
        if bug['status'] == 'closed':
            closed_count += 1
            
     # Count bugs in each category (UI, Backend, etc.)
    category_dist = {}
    for bug in bugs:
        category = bug['category']
    
    # If category not in dictionary, start with 0
        if category not in category_dist:
            category_dist[category] = 0

        # Increase category count by 1
        category_dist[category] += 1       
    
    colors = {
        'UI': "#2793db",
        'Backend': "#e76a3c",
        'Performance': '#f39c12',
        'Security': "#bc93cd",
        'Database': "#57c5af",
        'API': "#32506e",
        'Other': "#809fa1"
    }
    
    recent = sorted(bugs, key=lambda x: x['id'], reverse=True)[:5]
          
    return render_template('dashboard.html',
                                 title='Dashboard',
                                 total_bugs=total,
                                 open_bugs=open_count,
                                 in_progress_bugs=progress_count,
                                 closed_bugs=closed_count,
                                 category_dist=category_dist,
                                 colors=colors,
                                 recent_bugs=recent)

@app.route('/report', methods=['GET', 'POST'])
def report_bug():
    global bug_id_counter
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        severity = request.form.get('severity')
        attachment = request.files.get('attachment')
        
        attachment_name = None
        if attachment and attachment.filename:
            attachment_name = attachment.filename
        
        bug = {
            'id': bug_id_counter,
            'title': title,
            'description': description,
            'category': category,
            'severity': severity,
            'status': 'open',
            'assigned_to': None,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'attachment': attachment_name
        }
        
        bugs.append(bug)
        bug_id_counter += 1
        
        return redirect(url_for('dashboard'))
    
    #template = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', REPORT_BUG_TEMPLATE)
    return render_template('report_bug.html', title='Report Bug')

@app.route('/bugs')
def all_bugs():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    severity = request.args.get('severity', '')
    status = request.args.get('status', '')
    assigned = request.args.get('assigned', '')
    
    filtered = bugs.copy()
    
    if search:
        filtered = [b for b in filtered if search.lower() in b['title'].lower() or search.lower() in b['description'].lower()]
    
    if category:
        filtered = [b for b in filtered if b['category'] == category]
    
    if severity:
        filtered = [b for b in filtered if b['severity'] == severity]
    
    if status:
        filtered = [b for b in filtered if b['status'] == status]
    
    if assigned:
        if assigned == 'Unassigned':
            filtered = [b for b in filtered if not b['assigned_to']]
        else:
            filtered = [b for b in filtered if b['assigned_to'] == assigned]
    
    filtered = sorted(filtered, key=lambda x: x['id'], reverse=True)
    
    #template = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', ALL_BUGS_TEMPLATE)
    
    return render_template('all_bug.html',
                                 title='All Bugs',
                                 filtered_bugs=filtered,
                                 total_bugs=len(bugs),
                                 search=search,
                                 category=category,
                                 severity=severity,
                                 status=status,
                                 assigned=assigned,
                                 users=users)

@app.route('/bug/<int:bug_id>')
def bug_detail(bug_id):
    bug = next((b for b in bugs if b['id'] == bug_id), None)
    if not bug:
        return redirect(url_for('dashboard'))
    
    message = session.pop('message', None)
    
    # Get comments for this bug
    bug_comments = [c for c in comments if c['bug_id'] == bug_id]
    bug_comments = sorted(bug_comments, key=lambda x: x['id'])
    
    return render_template('bug_detail.html',
                                 title=f'Bug #{bug_id}',
                                 bug=bug,
                                 users=users,
                                 message=message)

@app.route('/bug/<int:bug_id>/assign', methods=['POST'])
def assign_bug(bug_id):
    bug = next((b for b in bugs if b['id'] == bug_id), None)
    if bug:
        assigned_to = request.form.get('assigned_to')
        bug['assigned_to'] = assigned_to
        session['message'] = f'Bug assigned to {assigned_to}'
    
    return redirect(url_for('bug_detail', bug_id=bug_id))

@app.route('/bug/<int:bug_id>/status', methods=['POST'])
def update_status(bug_id):
    bug = next((b for b in bugs if b['id'] == bug_id), None)
    if bug:
        new_status = request.form.get('status')
        bug['status'] = new_status
        session['message'] = f'Status updated to {new_status}'
    
    return redirect(url_for('bug_detail', bug_id=bug_id))

@app.route('/bug/<int:bug_id>/delete', methods=['POST'])
def delete_bug(bug_id):
    global bugs
    bugs = [b for b in bugs if b['id'] != bug_id]
    # Also delete all comments for this bug
    comments = [c for c in comments if c['bug_id'] != bug_id]
    return redirect(url_for('dashboard'))
    
    
    
@app.route('/bug/<int:bug_id>/comment', methods=['POST'])
def add_comment(bug_id):
    global comment_id_counter
    
    bug = next((b for b in bugs if b['id'] == bug_id), None)
    if bug:
        author = request.form.get('author')
        comment_text = request.form.get('comment')
        
        if author and comment_text:
            comment = {
                'id': comment_id_counter,
                'bug_id': bug_id,
                'author': author,
                'text': comment_text,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            comments.append(comment)
            comment_id_counter += 1
            session['message'] = 'Comment added successfully'
    
    return redirect(url_for('bug_detail', bug_id=bug_id))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    global comments
    
    comment = next((c for c in comments if c['id'] == comment_id), None)
    if comment:
        bug_id = comment['bug_id']
        comments = [c for c in comments if c['id'] != comment_id]
        session['message'] = 'Comment deleted successfully'
        return redirect(url_for('bug_detail', bug_id=bug_id))
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)