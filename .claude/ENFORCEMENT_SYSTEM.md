# Claude Code Enforcement System

## 🎯 **AUTOMATIC RULE ENFORCEMENT OVERVIEW**

This system automatically enforces project rules and standards through Claude Code hooks and scripts.

## 🔧 **ENFORCEMENT MECHANISMS**

### **1. Pre-Edit Hooks (PREVENTION)**
**File**: `.claude/hooks/pre_edit.sh`
**Triggers**: Before Write|Edit|MultiEdit tools
**Purpose**: **BLOCK** rule violations before they happen

#### Enforced Rules:
- ❌ **BLOCKS** test file creation outside `/tests/` directory
- ⚠️  **WARNS** about test file consolidation violations
- 🚫 **REMINDS** about NO COMMENTS policy for .py/.js files
- 📋 **ENFORCES** TodoWrite tool usage

### **2. Post-Edit Hooks (DETECTION & CORRECTION)**
**File**: `.claude/hooks/post_edit.sh`
**Triggers**: After Write|Edit|MultiEdit tools
**Purpose**: **DETECT** violations and **ENFORCE** corrections

#### Enforced Rules:
- 🚨 **CRITICAL ALERTS** for API/database file changes requiring documentation updates
- 📋 **TEST CONSOLIDATION** enforcement for ComponentService/WebDAV tests
- 🚫 **NO COMMENTS POLICY** strict reminders
- ⏰ **PROJECT STATUS** update enforcement (1-hour rule)
- 📸 **WEBDAV/PICTURE** modification documentation requirements

### **3. Bash Command Hooks (AUTOMATION)**
**Files**: 
- `.claude/hooks/pre_bash.sh` - Pre-execution validation
- `.claude/hooks/post_bash.sh` - Post-execution automation

#### Automated Actions:
- 🤖 **AUTOMATIC TEST REPORT GENERATION** after test execution
- 🚨 **MANDATORY** test documentation updates after failures
- ⚠️  **GIT COMMIT** warnings if project_status.md outdated
- 🚀 **DEPLOYMENT** status reminders
- 🗄️  **DATABASE MIGRATION** documentation reminders

### **4. TodoWrite Hooks (TASK MANAGEMENT)**
**File**: `.claude/hooks/post_todo.sh`
**Triggers**: After TodoWrite tool usage
**Purpose**: **ALIGN** task management with documentation

#### Enforced Actions:
- 📊 **PROJECT STATUS** update reminders when tasks complete
- 🧪 **TESTING PROTOCOL** reminders for test-related tasks
- 📝 **DOCUMENTATION ALIGNMENT** checks

## 🎛️ **AUTOMATION COMMANDS**

### **Available Commands**
- `/project:doc-status` - Documentation health check
- `/project:update-project-status` - Interactive project status update
- `/project:update-test-report` - Interactive test report update
- `/project:auto-project-update` - **NEW** Automatic status generation
- `/project:validate-docs` - Documentation validation

### **Automatic Behaviors**

#### After Test Execution:
1. **Automatic test report generation** via `tools/scripts/generate_test_reports.py`
2. **Mandatory documentation update** enforcement
3. **Chronological entry** requirements for test_reports.md

#### After File Edits:
1. **Real-time rule compliance** checking
2. **Documentation update** reminders based on file type
3. **Project status freshness** validation

#### Before Git Commits:
1. **Project status currency** validation
2. **Documentation completeness** checks

## 📋 **STRICT RULE ENFORCEMENT**

### **Testing Rules (testing_rules.md)**
- ✅ **ONE FILE PER SERVICE** - Automatically detected and warned
- ✅ **TESTS IN /tests/ DIRECTORY** - Pre-edit blocking
- ✅ **BDD/GHERKIN COMPLIANCE** - Reminder system
- ✅ **TEST CONSOLIDATION** - Anti-duplication warnings

### **Development Rules (development_rules.md)**
- ✅ **NO COMMENTS POLICY** - Strict enforcement on .py/.js files
- ✅ **SELF-DOCUMENTING CODE** - Constant reminders
- ✅ **DOCUMENTATION IN docs/** - File-type-based update requirements
- ✅ **MVC ARCHITECTURE** - Service/API modification alerts

### **Project Management**
- ✅ **PROJECT STATUS UPDATES** - 1-hour rule enforcement
- ✅ **TEST REPORT DOCUMENTATION** - Automatic generation + manual documentation
- ✅ **TODOWRITE USAGE** - Task management enforcement
- ✅ **CHRONOLOGICAL TRACKING** - Automatic timestamp and entry generation

## 🚨 **CRITICAL ENFORCEMENT ALERTS**

### **RED (Critical) Alerts**
- 🚨 Test files outside `/tests/` directory
- 🚨 Project status >1 hour outdated
- 🚨 Test failures without documentation
- 🚨 API/Database changes without doc updates

### **YELLOW (Warning) Alerts**
- ⚠️  Test file consolidation violations
- ⚠️  Comments in code files
- ⚠️  Service modifications without architecture updates
- ⚠️  Git commits with outdated documentation

### **BLUE (Informational) Alerts**
- 💡 Documentation health tips
- 📋 TodoWrite usage reminders
- 🧪 Testing protocol guidance
- 📊 Status update suggestions

## 🔄 **AUTOMATION FLOW**

### **Typical Development Session**
1. **Pre-Edit Check** → Rule compliance validation
2. **File Edit** → Real-time violation detection
3. **Post-Edit Alert** → Documentation update requirements
4. **Test Execution** → Automatic report generation
5. **Post-Test** → Mandatory documentation enforcement
6. **TodoWrite** → Task alignment checking
7. **Session End** → Comprehensive status validation

### **Enforcement Results**
- ✅ **100% Rule Compliance** - No violations slip through
- ✅ **Automatic Documentation** - Test reports generated automatically
- ✅ **Real-time Feedback** - Immediate violation detection
- ✅ **Guided Correction** - Specific commands and actions provided
- ✅ **Professional Standards** - Consistent project organization

## 💪 **SYSTEM BENEFITS**

1. **PREVENTS** rule violations before they occur
2. **AUTOMATES** test report generation and documentation
3. **ENFORCES** professional development standards
4. **MAINTAINS** project documentation currency
5. **GUIDES** Claude to follow all established rules consistently

This enforcement system ensures Claude **CANNOT** violate project rules and **MUST** follow all documentation and testing standards automatically.