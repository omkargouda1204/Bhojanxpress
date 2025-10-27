// BhojanXpress Admin Common JavaScript Functions

// Commission Payment Modal Functions
function showPaymentModal(orderId) {
    // Create the payment modal if it doesn't exist
    if (!document.getElementById('paymentModal')) {
        createPaymentModal();
    }
    
    // Set the form action
    const paymentForm = document.getElementById('paymentForm');
    if (paymentForm) {
        paymentForm.action = `/admin/pay-commission?order_id=${orderId}`;
    }
    
    // Show the modal using Bootstrap
    const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
    modal.show();
}

function showPayAllModal(agentId) {
    // Create the pay all modal if it doesn't exist
    if (!document.getElementById('payAllModal')) {
        createPayAllModal();
    }
    
    // Set the form action
    const payAllForm = document.getElementById('payAllForm');
    if (payAllForm) {
        payAllForm.action = `/admin/pay-all-commission/${agentId}`;
    }
    
    // Show the modal using Bootstrap
    const modal = new bootstrap.Modal(document.getElementById('payAllModal'));
    modal.show();
}

function createPaymentModal() {
    const modalHtml = `
        <div class="modal fade" id="paymentModal" tabindex="-1" aria-labelledby="paymentModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title" id="paymentModalLabel">
                            <i class="fas fa-money-bill-wave"></i> Commission Payment
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <form id="paymentForm" method="POST">
                        <div class="modal-body">
                            <input type="hidden" name="csrf_token" value="${getCSRFToken()}"/>
                            
                            <div class="mb-3">
                                <label for="payment_method" class="form-label">Payment Method</label>
                                <select class="form-select" id="payment_method" name="payment_method" onchange="toggleReferenceField()" required>
                                    <option value="">Select Payment Method</option>
                                    <option value="cash">Cash Payment</option>
                                    <option value="online">Online Payment</option>
                                </select>
                            </div>
                            
                            <div class="mb-3" id="referenceGroup" style="display: none;">
                                <label for="reference_id" class="form-label">Reference Number</label>
                                <input type="text" class="form-control" id="reference_id" name="reference_id" 
                                       placeholder="Enter transaction/reference number">
                                <small class="form-text text-muted">Required for online payments</small>
                            </div>
                            
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle"></i>
                                <strong>Note:</strong> This action will mark the commission as paid and cannot be undone.
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-success">
                                <i class="fas fa-check"></i> Process Payment
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Add form validation
    document.getElementById('paymentForm').addEventListener('submit', function(e) {
        const paymentMethod = document.getElementById('payment_method').value;
        const referenceId = document.getElementById('reference_id').value.trim();
        
        if (!paymentMethod) {
            e.preventDefault();
            alert('Please select a payment method');
            return false;
        }
        
        if (paymentMethod === 'online' && !referenceId) {
            e.preventDefault();
            alert('Reference number is required for online payments');
            return false;
        }
        
        const confirmMessage = paymentMethod === 'cash' ? 
            'Are you sure you want to mark this commission as paid in cash?' :
            `Are you sure you want to process this online payment with reference: ${referenceId}?`;
            
        if (!confirm(confirmMessage)) {
            e.preventDefault();
            return false;
        }
    });
}

function createPayAllModal() {
    const modalHtml = `
        <div class="modal fade" id="payAllModal" tabindex="-1" aria-labelledby="payAllModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-success text-white">
                        <h5 class="modal-title" id="payAllModalLabel">
                            <i class="fas fa-money-bill-wave"></i> Pay All Commissions
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <form id="payAllForm" method="POST">
                        <div class="modal-body">
                            <input type="hidden" name="csrf_token" value="${getCSRFToken()}"/>
                            
                            <div class="alert alert-warning">
                                <i class="fas fa-exclamation-triangle"></i>
                                <strong>Warning:</strong> This will pay commission for all delivered orders for this agent.
                            </div>
                            
                            <div class="mb-3">
                                <label for="pay_all_payment_method" class="form-label">Payment Method</label>
                                <select class="form-select" id="pay_all_payment_method" name="payment_method" onchange="togglePayAllReferenceField()" required>
                                    <option value="">Select Payment Method</option>
                                    <option value="cash">Cash Payment</option>
                                    <option value="online">Online Payment</option>
                                </select>
                            </div>
                            
                            <div class="mb-3" id="payAllReferenceGroup" style="display: none;">
                                <label for="pay_all_reference_id" class="form-label">Reference Number</label>
                                <input type="text" class="form-control" id="pay_all_reference_id" name="reference_id" 
                                       placeholder="Enter transaction/reference number">
                                <small class="form-text text-muted">Required for online payments</small>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-success">
                                <i class="fas fa-check"></i> Pay All Commissions
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Add form validation
    document.getElementById('payAllForm').addEventListener('submit', function(e) {
        const paymentMethod = document.getElementById('pay_all_payment_method').value;
        const referenceId = document.getElementById('pay_all_reference_id').value.trim();
        
        if (!paymentMethod) {
            e.preventDefault();
            alert('Please select a payment method');
            return false;
        }
        
        if (paymentMethod === 'online' && !referenceId) {
            e.preventDefault();
            alert('Reference number is required for online payments');
            return false;
        }
        
        const confirmMessage = paymentMethod === 'cash' ? 
            'Are you sure you want to pay all commissions in cash?' :
            `Are you sure you want to process all payments online with reference: ${referenceId}?`;
            
        if (!confirm(confirmMessage)) {
            e.preventDefault();
            return false;
        }
    });
}

function toggleReferenceField() {
    const paymentMethod = document.getElementById('payment_method').value;
    const referenceGroup = document.getElementById('referenceGroup');
    const referenceInput = document.getElementById('reference_id');
    
    if (paymentMethod === 'online') {
        referenceGroup.style.display = 'block';
        referenceInput.setAttribute('required', 'true');
    } else {
        referenceGroup.style.display = 'none';
        referenceInput.removeAttribute('required');
        referenceInput.value = '';
    }
}

function togglePayAllReferenceField() {
    const paymentMethod = document.getElementById('pay_all_payment_method').value;
    const referenceGroup = document.getElementById('payAllReferenceGroup');
    const referenceInput = document.getElementById('pay_all_reference_id');
    
    if (paymentMethod === 'online') {
        referenceGroup.style.display = 'block';
        referenceInput.setAttribute('required', 'true');
    } else {
        referenceGroup.style.display = 'none';
        referenceInput.removeAttribute('required');
        referenceInput.value = '';
    }
}

function getCSRFToken() {
    const csrfInput = document.querySelector('[name=csrf_token]');
    return csrfInput ? csrfInput.value : '';
}

// Global error handler for missing functions
window.addEventListener('error', function(e) {
    if (e.message.includes('showPaymentModal') || e.message.includes('showPayAllModal')) {
        console.warn('Payment modal functions loaded from admin-common.js');
    }
});