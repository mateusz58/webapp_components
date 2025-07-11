# Instructions for User

## How to Effectively Communicate with Claude

### Quick Communication Guide

#### ✅ Good Request Examples
```
"The picture visibility issue is still occurring. Check the AJAX refresh in alpine-component-detail.js line 120. High priority."

"Add validation to the component form for required fields. Follow the existing pattern in component_routes.py. Include CSRF protection."

"Database query in component_detail route is slow. Optimize with selectinload pattern from development_rules.md."
```

#### ❌ Poor Request Examples
```
"Fix the pictures"
"Make it faster" 
"Add validation"
```

### Current Critical Issue
**Picture Visibility Problem**: Component variant pictures don't appear immediately after creation/editing. AJAX solution implemented but needs manual validation.

### When Reporting Issues Include
- **Exact steps** to reproduce
- **Expected vs actual** behavior  
- **Browser/version** used
- **Console errors** (F12 Developer Tools)
- **Screenshots** if visual

### Quick Reference

#### Key Files
- `CLAUDE.md` - Master documentation
- `docs/project_status.md` - Current issues  
- `app/web/component_routes.py` - Main logic
- `app/static/js/components/alpine-component-detail.js` - Frontend

#### Common Commands
```bash
./restart.sh              # Restart application
docker-compose logs       # View logs  
./start.sh status        # Check status
```

#### Testing Checklist After Changes
- [ ] Restart application: `./restart.sh`
- [ ] Test picture visibility on component creation/edit
- [ ] Check browser console for errors (F12)
- [ ] Verify AJAX refresh works

### Communication Tips

#### Be Specific About
- **File names and line numbers** when possible
- **Priority level** (critical/high/medium/low)
- **Testing requirements** (manual/automated)
- **Relationship to picture visibility issue**

#### Context to Provide
- Which part of system (component management, pictures, database, etc.)
- If this is a new feature or bug fix
- Performance requirements if applicable
- Any deadline or urgency

### System Status
- ✅ Core functionality working
- ✅ Performance optimizations active
- ⚠️ Picture visibility needs validation  
- ✅ Security measures in place