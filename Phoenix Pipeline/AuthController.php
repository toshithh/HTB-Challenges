<?php
require_once __DIR__ . '/../Models/Database.php';

class AuthController {
    public static function showLogin() {
        require __DIR__ . '/../Views/login.php';
    }
    public static function showRegister() {
        require __DIR__ . '/../Views/register.php';
    }
    public static function login() {
        $db = Database::getInstance()->getConnection();
        $username = $_POST['username'] ?? '';
        $password = $_POST['password'] ?? '';
        $stmt = $db->prepare('SELECT * FROM users WHERE username = ?');
        $stmt->execute([$username]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);
        if ($user && password_verify($password, $user['password'])) {
            $_SESSION['username'] = $user['username'];
            $_SESSION['area'] = $user['area'];
            header('Location: ' . ($user['username'] === 'admin' ? '/challenge/admin' : '/challenge/operator'));
            exit;
        }
        $error = 'Invalid credentials';
        require __DIR__ . '/../Views/login.php';
    }
    public static function logout() {
        session_unset();
        session_destroy();
        header('Location: /challenge/login');
        exit;
    }
    public static function register() {
        $db = Database::getInstance()->getConnection();
        $username = $_POST['username'] ?? '';
        $password = $_POST['password'] ?? '';
        $area = $_POST['area'] ?? '';
        
        // Set the session so user can login immediately after registration
        $_SESSION['username'] = $username;
        $_SESSION['area'] = $area;
        
        $stmt = $db->prepare('SELECT * FROM users WHERE username = ?');
        $stmt->execute([$username]);
        if ($stmt->fetch()) {
            header('Location: /challenge/username-exists');
            exit;
        }
        
        $hash = password_hash($password, PASSWORD_DEFAULT);
        $stmt = $db->prepare('INSERT INTO users (username, password, role, area) VALUES (?, ?, ?, ?)');
        $stmt->execute([$username, $hash, 'operator', $area]);
        header('Location: /challenge/operator');
        exit;
    }
    public static function usernameExists() {
        unset($_SESSION['username'], $_SESSION['area']);
        require __DIR__ . '/../Views/username_exists.php';
    }
} 