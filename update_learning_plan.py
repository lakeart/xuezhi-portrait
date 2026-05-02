"""
学习计划页面增强脚本
修复标记完成按钮并添加手动修改功能
"""
import re

def update_learning_plan_html():
    # 读取原文件
    with open('d:/桌面/1/app/templates/student/learning_plan_v2.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修复标记完成函数
    old_mark_complete = """// 标记完成
function markAsComplete() {
    showToast('任务已标记完成！');
    var modal = bootstrap.Modal.getInstance(document.getElementById('planDetailModal'));
    if (modal) modal.hide();
}"""
    
    new_mark_complete = """// 标记完成 - 增强版
let completedTasks = new Set();

function markAsComplete(topic, day) {
    // 使用AJAX保存到服务器
    fetch('/student/api/mark-complete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            topic: topic,
            day: day
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 更新本地记录
            const taskKey = topic + '-' + day;
            completedTasks.add(taskKey);
            
            // 更新UI
            const taskElement = document.querySelector(`[data-topic="${topic}"][data-day="${day}"]`);
            if (taskElement) {
                taskElement.classList.add('task-completed');
                taskElement.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <i class="fas fa-check-circle text-success me-2"></i>
                            <strong>${topic}</strong>
                        </div>
                        <span class="badge bg-success">
                            <i class="fas fa-check me-1"></i>已完成
                        </span>
                    </div>
                `;
            }
            
            showToast(data.message || '任务已标记完成！', 'success');
            
            // 关闭模态框
            var modal = bootstrap.Modal.getInstance(document.getElementById('planDetailModal'));
            if (modal) modal.hide();
            
            // 更新统计
            updateCompletionStats();
        } else {
            showToast('标记失败：' + (data.error || '未知错误'), 'error');
        }
    })
    .catch(error => {
        console.error('标记完成失败:', error);
        showToast('标记完成失败，请重试', 'error');
    });
}"""
    
    content = content.replace(old_mark_complete, new_mark_complete)
    
    # 2. 添加手动修改计划功能
    old_modal_footer = """<div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                <button type="button" class="btn btn-success" onclick="markAsComplete()">
                    <i class="fas fa-check me-1"></i>标记完成
                </button>
            </div>"""
    
    new_modal_footer = """<div class="modal-footer d-flex justify-content-between">
                <div>
                    <button type="button" class="btn btn-outline-primary" onclick="showEditPlanModal()">
                        <i class="fas fa-edit me-1"></i>修改计划
                    </button>
                </div>
                <div>
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    <button type="button" class="btn btn-success" id="confirmMarkComplete">
                        <i class="fas fa-check me-1"></i>标记完成
                    </button>
                </div>
            </div>"""
    
    content = content.replace(old_modal_footer, new_modal_footer)
    
    # 3. 添加修改计划的模态框
    edit_modal = """
<!-- 修改学习计划模态框 -->
<div class="modal fade" id="editPlanModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header bg-primary text-white">
                <h5 class="modal-title">
                    <i class="fas fa-edit me-2"></i>编辑学习计划
                </h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    您可以自定义修改学习时间分配，系统会根据您的调整重新优化计划
                </div>
                
                <form id="editPlanForm">
                    <div class="mb-3">
                        <label class="form-label fw-bold">知识点</label>
                        <input type="text" class="form-control" id="editTopicName" readonly>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">学习时长（分钟）</label>
                            <select class="form-select" id="editDuration">
                                <option value="30">30 分钟</option>
                                <option value="45" selected>45 分钟</option>
                                <option value="60">60 分钟</option>
                                <option value="90">90 分钟</option>
                                <option value="120">120 分钟</option>
                            </select>
                        </div>
                        
                        <div class="col-md-6 mb-3">
                            <label class="form-label">优先级</label>
                            <select class="form-select" id="editPriority">
                                <option value="P0">P0 - 紧急优先</option>
                                <option value="P1">P1 - 重要</option>
                                <option value="P2">P2 - 常规</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">安排到</label>
                        <select class="form-select" id="editDay">
                            <option value="周一">周一</option>
                            <option value="周二">周二</option>
                            <option value="周三">周三</option>
                            <option value="周四">周四</option>
                            <option value="周五">周五</option>
                            <option value="周六">周六</option>
                            <option value="周日">周日</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">学习方式</label>
                        <select class="form-select" id="editMethod">
                            <option value="视频学习">视频学习</option>
                            <option value="强化练习">强化练习</option>
                            <option value="复习巩固">复习巩固</option>
                            <option value="综合学习">综合学习</option>
                        </select>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                <button type="button" class="btn btn-primary" onclick="savePlanChanges()">
                    <i class="fas fa-save me-1"></i>保存修改
                </button>
            </div>
        </div>
    </div>
</div>

<!-- 添加自定义任务模态框 -->
<div class="modal fade" id="addCustomTaskModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header bg-success text-white">
                <h5 class="modal-title">
                    <i class="fas fa-plus me-2"></i>添加自定义任务
                </h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label class="form-label">任务名称</label>
                    <input type="text" class="form-control" id="customTaskName" placeholder="输入自定义学习任务">
                </div>
                
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">时长（分钟）</label>
                        <input type="number" class="form-control" id="customTaskDuration" value="45" min="15" max="180">
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">安排日期</label>
                        <input type="date" class="form-control" id="customTaskDate">
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                <button type="button" class="btn btn-success" onclick="addCustomTask()">
                    <i class="fas fa-plus me-1"></i>添加任务
                </button>
            </div>
        </div>
    </div>
</div>"""
    
    # 在 </div></div></div>{% endblock %} 前添加模态框
    insert_position = content.find("{% endblock %}")
    if insert_position != -1:
        content = content[:insert_position] + edit_modal + "\n" + content[insert_position:]
    
    # 4. 添加修改计划的JavaScript函数
    old_scripts_end = """// 隐藏加载动画
function hideLoadingAnimations() {"""
    
    new_scripts = """// 显示编辑计划模态框
let currentEditingTopic = null;
let currentEditingDay = null;

function showEditPlanModal(topic, day) {
    currentEditingTopic = topic;
    currentEditingDay = day;
    
    // 填充当前数据
    document.getElementById('editTopicName').value = topic || '';
    
    // 显示模态框
    var modal = new bootstrap.Modal(document.getElementById('editPlanModal'));
    modal.show();
}

function savePlanChanges() {
    const topic = document.getElementById('editTopicName').value;
    const duration = document.getElementById('editDuration').value;
    const priority = document.getElementById('editPriority').value;
    const day = document.getElementById('editDay').value;
    const method = document.getElementById('editMethod').value;
    
    // 发送到服务器
    fetch('/student/api/update-plan-item', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            topic: topic,
            duration: parseInt(duration),
            priority: priority,
            day: day,
            method: method
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('计划已更新！', 'success');
            
            // 关闭编辑模态框
            var editModal = bootstrap.Modal.getInstance(document.getElementById('editPlanModal'));
            if (editModal) editModal.hide();
            
            // 关闭详情模态框
            var detailModal = bootstrap.Modal.getInstance(document.getElementById('planDetailModal'));
            if (detailModal) detailModal.hide();
            
            // 重新加载计划数据
            loadLearningPlanData();
        } else {
            showToast('更新失败：' + (data.error || '未知错误'), 'error');
        }
    })
    .catch(error => {
        console.error('保存失败:', error);
        showToast('保存失败，请重试', 'error');
    });
}

function addCustomTask() {
    const taskName = document.getElementById('customTaskName').value;
    const duration = document.getElementById('customTaskDuration').value;
    const date = document.getElementById('customTaskDate').value;
    
    if (!taskName) {
        showToast('请输入任务名称', 'error');
        return;
    }
    
    // 这里应该发送到服务器保存
    showToast('自定义任务已添加！', 'success');
    
    // 关闭模态框
    var modal = bootstrap.Modal.getInstance(document.getElementById('addCustomTaskModal'));
    if (modal) modal.hide();
    
    // 清空表单
    document.getElementById('customTaskName').value = '';
    document.getElementById('customTaskDuration').value = '45';
}

function updateCompletionStats() {
    const total = document.querySelectorAll('.day-cell .bg-light').length;
    const completed = document.querySelectorAll('.task-completed').length;
    
    const progressBar = document.querySelector('.learning-progress .progress-bar');
    if (progressBar && total > 0) {
        const percentage = Math.round((completed / total) * 100);
        progressBar.style.width = percentage + '%';
        progressBar.textContent = percentage + '%';
    }
}"""
    
    content = content.replace(old_scripts_end, new_scripts + "\n" + old_scripts_end)
    
    # 5. 修改showPlanDetail函数以支持动态按钮
    old_show_detail = """// 显示计划详情
function showPlanDetail(topic, mastery, priority, method) {
    var content = '<div class=\"mb-3\">';"""
    
    new_show_detail = """// 显示计划详情
let currentPlanDetail = null;

function showPlanDetail(topic, mastery, priority, method, duration, day) {
    // 保存当前详情数据
    currentPlanDetail = {topic, mastery, priority, method, duration, day};
    
    var content = '<div class=\"mb-3\">';"""
    
    content = content.replace(old_show_detail, new_show_detail)
    
    # 6. 修改详情中的标记完成按钮
    old_detail_footer = """<button type=\"button\" class=\"btn btn-success\" id=\"confirmMarkComplete\">
                    <i class=\"fas fa-check me-1\"></i>标记完成
                </button>"""
    
    new_detail_footer = """<button type="button" class="btn btn-success" id="confirmMarkComplete" onclick="confirmMarkComplete()">
                    <i class="fas fa-check me-1"></i>标记完成
                </button>"""
    
    content = content.replace(old_detail_footer, new_detail_footer)
    
    # 7. 添加confirmMarkComplete函数
    old_confirm_button = """</script>"""
    
    new_confirm_function = """// 确认标记完成
function confirmMarkComplete() {
    if (currentPlanDetail) {
        markAsComplete(currentPlanDetail.topic, currentPlanDetail.day);
    } else {
        markAsComplete();
    }
}

// 初始化确认按钮点击事件
document.addEventListener('DOMContentLoaded', function() {
    const confirmBtn = document.getElementById('confirmMarkComplete');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', confirmMarkComplete);
    }
});

</script>"""
    
    content = content.replace(old_confirm_button, new_confirm_function)
    
    # 8. 添加完成任务的样式
    styles = """
<style>
    /* 完成任务样式 */
    .task-completed {
        opacity: 0.7;
        text-decoration: line-through;
        background-color: #d4edda !important;
    }
    
    .task-completed strong {
        color: #28a745;
    }
    
    /* 日历任务样式 */
    .day-cell .task-item {
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .day-cell .task-item:hover {
        transform: scale(1.02);
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    
    /* 编辑模态框增强 */
    #editPlanModal .form-label {
        color: #495057;
        font-weight: 600;
    }
    
    /* 加载动画 */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(0,123,255,.3);
        border-radius: 50%;
        border-top-color: #007bff;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
</style>"""
    
    # 在 </style> 前添加
    insert_pos = content.rfind('</style>')
    if insert_pos != -1:
        content = content[:insert_pos] + styles + "\n" + content[insert_pos:]
    
    # 保存文件
    with open('d:/桌面/1/app/templates/student/learning_plan_v2.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("学习计划页面增强完成！")

if __name__ == '__main__':
    update_learning_plan_html()
