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

    // Raw inputs
    $username_raw = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    $area = $_POST['area'] ?? '';

    // Normalize and validate username
    $username = trim($username_raw);
    // Basic whitelist: letters, digits, dot, underscore, hyphen. Length 3..32
    if (!preg_match('/^[A-Za-z0-9._-]{3,32}$/', $username)) {
        // Keep behavior simple: redirect to username-exists (or you can create a new page)
        header('Location: /challenge/username-exists');
        exit;
    }

    // Basic password policy (adjust as needed)
    if (!is_string($password) || strlen($password) < 6) {
        header('Location: /challenge/username-exists');
        exit;
    }

    // Reserved usernames — case-insensitive
    $reserved = ['admin', 'administrator', 'root', 'system'];
    $lower = strtolower($username);
    foreach ($reserved as $r) {
        if ($lower === strtolower($r)) {
            header('Location: /challenge/username-exists');
            exit;
        }
    }

    try {
        // Use transaction to reduce race windows
        $db->beginTransaction();

        // Case-insensitive uniqueness check
        $stmt = $db->prepare('SELECT 1 FROM users WHERE LOWER(username) = LOWER(?) LIMIT 1');
        $stmt->execute([$username]);
        if ($stmt->fetchColumn()) {
            $db->rollBack();
            header('Location: /challenge/username-exists');
            exit;
        }

        // Hash password
        $hash = password_hash($password, PASSWORD_DEFAULT);

        // Insert user. role is fixed server-side.
        $stmt = $db->prepare('INSERT INTO users (username, password, role, area) VALUES (?, ?, ?, ?)');
        $stmt->execute([$username, $hash, 'operator', $area]);

        $db->commit();

        // Set the session so user can login immediately after registration
        // Regenerate session id to prevent session fixation
        if (session_status() !== PHP_SESSION_ACTIVE) {
            session_start();
        }
        session_regenerate_id(true);
        $_SESSION['username'] = $username;
        $_SESSION['area'] = $area;

        header('Location: /challenge/operator');
        exit;
    } catch (PDOException $e) {
        // Roll back if in transaction
        if ($db->inTransaction()) {
            $db->rollBack();
        }

        // If a duplicate key was inserted by a concurrent request, treat as username exists.
        // Many DB engines provide vendor-specific SQLSTATE/code for unique constraint violation.
        // We defensively treat any PDOException here as "username exists" to avoid leaking info.
        header('Location: /challenge/username-exists');
        exit;
    } catch (Exception $e) {
        if ($db->inTransaction()) {
            $db->rollBack();
        }
        // General fallback
        header('Location: /challenge/username-exists');
        exit;
    }
}

    public static function usernameExists() {
        unset($_SESSION['username'], $_SESSION['area']);
        require __DIR__ . '/../Views/username_exists.php';
    }
} 