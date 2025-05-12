document.addEventListener('DOMContentLoaded', function() {
    var form = document.querySelector('.login-form');

    if (!form) return;

    function validateForm(event) {
        event.preventDefault();

        var name = form.querySelector('#name')?.value.trim();
        var cpf = form.querySelector('#cpf')?.value.trim();
        var username = form.querySelector('#username')?.value.trim();
        var password = form.querySelector('#password')?.value.trim();
        var cellphone = form.querySelector('#cellphone')?.value.trim();
        var loja = form.querySelector('#loja')?.value;

        if (name && name.length < 3) {
            alert('Nome deve ter pelo menos 3 caracteres.');
            return false;
        }

        // Se CPF estiver preenchido, valida
        if (cpf && cpf.replace(/\D/g, '').length !== 11 && cpf !== '') {
            alert('CPF inválido. Deve conter 11 dígitos.');
            return false;
        }

        var emailPattern = /^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$/i;
        if (username && !emailPattern.test(username)) {
            alert('Email inválido.');
            return false;
        }

        if (password && password.length < 6) {
            alert('Senha deve ter pelo menos 6 caracteres.');
            return false;
        }

        if (cellphone && cellphone.length < 8) {
            alert('Telefone inválido.');
            return false;
        }

        form.submit();
    }

    form.addEventListener('submit', validateForm);
});
