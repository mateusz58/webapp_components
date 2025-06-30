"""Admin utility routes for WebDAV management and system status."""

from flask import Blueprint, jsonify, render_template_string, current_app
from app.utils.webdav_utils import get_webdav_status, log_webdav_status
import os

admin_web = Blueprint('admin_web', __name__, url_prefix='/admin')


@admin_web.route('/webdav-status')
def webdav_status():
    """Check WebDAV mount status and provide troubleshooting info."""
    status = get_webdav_status()
    
    # Create a simple HTML page with status
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebDAV Status - Component Management</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 2rem; }
            .status { padding: 1rem; margin: 1rem 0; border-radius: 4px; }
            .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            .warning { background: #fff3cd; border: 1px solid #ffeeba; color: #856404; }
            .danger { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
            .info { background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }
            .code { background: #f8f9fa; padding: 0.5rem; font-family: monospace; border-radius: 4px; }
            h1 { color: #333; }
            h2 { color: #666; margin-top: 2rem; }
            ul { margin: 0.5rem 0; }
            li { margin: 0.25rem 0; }
        </style>
    </head>
    <body>
        <h1>WebDAV Status</h1>
        
        {% if status.is_mounted %}
        <div class="status success">
            <strong>✓ WebDAV is properly mounted</strong>
            <ul>
                <li>Mount point: {{ status.mount_point }}</li>
                <li>Files available: {{ status.files_count }}</li>
                <li>Write access: {{ "Yes" if status.has_write_access else "No" }}</li>
            </ul>
        </div>
        {% else %}
        <div class="status danger">
            <strong>✗ WebDAV is NOT mounted</strong>
            <p>The application cannot save pictures to WebDAV storage.</p>
        </div>
        {% endif %}

        <h2>Configuration</h2>
        <div class="status info">
            <ul>
                <li><strong>Mount Point:</strong> {{ status.mount_point }}</li>
                <li><strong>Internal URL:</strong> {{ status.internal_url }}</li>
                <li><strong>External URL:</strong> {{ status.external_url }}</li>
                <li><strong>Mount exists:</strong> {{ "Yes" if status.mount_exists else "No" }}</li>
            </ul>
        </div>

        {% if status.issues %}
        <h2>Issues Detected</h2>
        <div class="status warning">
            <ul>
                {% for issue in status.issues %}
                <li>{{ issue }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        <h2>Troubleshooting</h2>
        {% if not status.is_mounted %}
        <div class="status warning">
            <h3>To fix WebDAV mounting:</h3>
            <ol>
                <li>Run the mount script:
                    <div class="code">sudo ./mount-webdav-simple.sh</div>
                </li>
                <li>Or mount manually:
                    <div class="code">sudo mount -t davfs {{ status.internal_url }} {{ status.mount_point }}</div>
                </li>
                <li>Set permissions:
                    <div class="code">sudo chown -R 1000:1000 {{ status.mount_point }}<br>
                    sudo chmod -R 755 {{ status.mount_point }}</div>
                </li>
                <li>Restart the application after mounting</li>
            </ol>
        </div>
        {% endif %}

        <h2>Current Directory Contents</h2>
        {% if status.mount_exists %}
        <div class="status info">
            <strong>Contents of {{ status.mount_point }}:</strong>
            <div class="code">
                {% for file in directory_listing %}
                {{ file }}<br>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <p><a href="/component/new">← Back to New Component</a></p>
        <p><small>Last checked: {{ timestamp }}</small></p>
    </body>
    </html>
    """
    
    # Get directory listing
    directory_listing = []
    if status['mount_exists']:
        try:
            files = os.listdir(status['mount_point'])
            directory_listing = files[:20]  # Show first 20 files
            if len(files) > 20:
                directory_listing.append(f"... and {len(files) - 20} more files")
        except Exception as e:
            directory_listing = [f"Error reading directory: {e}"]
    
    from datetime import datetime
    
    return render_template_string(
        html_template, 
        status=status, 
        directory_listing=directory_listing,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )


@admin_web.route('/webdav-status.json')
def webdav_status_json():
    """Get WebDAV status as JSON."""
    status = get_webdav_status()
    log_webdav_status()
    return jsonify(status)


@admin_web.route('/system-info')
def system_info():
    """Get basic system information."""
    import subprocess
    
    info = {
        'mount_points': [],
        'davfs_installed': False,
        'components_folder_exists': os.path.exists('/components'),
        'upload_config': {
            'UPLOAD_FOLDER': current_app.config.get('UPLOAD_FOLDER'),
            'UPLOAD_URL_PREFIX': current_app.config.get('UPLOAD_URL_PREFIX'),
            'LOCAL_UPLOAD_FOLDER': current_app.config.get('LOCAL_UPLOAD_FOLDER')
        }
    }
    
    # Check if davfs2 is installed
    try:
        result = subprocess.run(['which', 'mount.davfs'], capture_output=True, text=True)
        info['davfs_installed'] = result.returncode == 0
    except:
        info['davfs_installed'] = False
    
    # Get mount points
    try:
        result = subprocess.run(['mount'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'davfs' in line or '/components' in line:
                    info['mount_points'].append(line.strip())
    except:
        pass
    
    return jsonify(info)