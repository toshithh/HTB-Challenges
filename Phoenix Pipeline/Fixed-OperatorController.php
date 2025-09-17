<?php
require_once __DIR__ . '/../Models/Database.php';

class OperatorController {
    public static function dashboard() {
        if (!isset($_SESSION['username']) || $_SESSION['username'] === 'admin') {
            header('Location: /challenge/login'); exit;
        }
        $db = Database::getInstance()->getConnection();
        $area = $_SESSION['area'] ?? '';
        $stmt = $db->prepare('SELECT * FROM infrastructure WHERE area = ? ORDER BY name');
        $stmt->execute([$area]);
        $infra = $stmt->fetchAll(PDO::FETCH_ASSOC);
        require __DIR__ . '/../Views/operator_dashboard.php';
    }
    public static function showReportForm() {
        if (!isset($_SESSION['username']) || $_SESSION['username'] === 'admin') {
            header('Location: /challenge/login'); exit;
        }
        $db = Database::getInstance()->getConnection();
        $area = $_SESSION['area'] ?? '';
        $stmt = $db->prepare('SELECT * FROM infrastructure WHERE area = ? ORDER BY name');
        $stmt->execute([$area]);
        $infra = $stmt->fetchAll(PDO::FETCH_ASSOC);
        require __DIR__ . '/../Views/report_form.php';
    }
    
public static function submitReport() {
    if (!isset($_SESSION['username']) || $_SESSION['username'] === 'admin') {
        header('Location: /challenge/login'); exit;
    }

    $db = Database::getInstance()->getConnection();
    $user_id = self::getUserId($_SESSION['username']);
    $infra_id = $_POST['infra_id'] ?? '';
    $description = $_POST['description'] ?? '';
    $area = $_SESSION['area'];

    $showFormWithError = function($errorMessage) use ($db, $area) {
        $error = $errorMessage;
        $stmt = $db->prepare('SELECT * FROM infrastructure WHERE area = ? ORDER BY name');
        $stmt->execute([$area]);
        $infra = $stmt->fetchAll(PDO::FETCH_ASSOC);
        require __DIR__ . '/../Views/report_form.php';
    };

    if (empty($infra_id) || empty($description)) {
        $showFormWithError('All fields are required.');
        return;
    }

    $stmt = $db->prepare('SELECT id FROM infrastructure WHERE id = ? AND area = ?');
    $stmt->execute([$infra_id, $area]);
    if (!$stmt->fetch()) {
        $showFormWithError('Invalid infrastructure selected.');
        return;
    }

    if (!isset($_FILES['photo']) || $_FILES['photo']['error'] !== UPLOAD_ERR_OK) {
        $showFormWithError('Photo documentation is required.');
        return;
    }

    $maxFileSize = 10 * 1024 * 1024; // 10MB
    if ($_FILES['photo']['size'] > $maxFileSize) {
        $showFormWithError('File size too large. Maximum allowed size is 10MB.');
        return;
    }

    $original = $_FILES['photo']['name'];
    $ext = strtolower(pathinfo($original, PATHINFO_EXTENSION));
    $tmp_name = $_FILES['photo']['tmp_name'];

    // Validate MIME type using finfo on the in-memory tmp_name
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $mime = finfo_file($finfo, $tmp_name);
    finfo_close($finfo);

    if (strpos($mime, 'image/') !== 0) {
        $showFormWithError('Invalid file type. Only image files are allowed.');
        return;
    }

    $allowed = ['jpg','jpeg','png','gif','bmp','webp'];
    if (!in_array($ext, $allowed)) {
        $showFormWithError('Invalid file extension. Only image files (JPG, PNG, GIF, BMP, WEBP) are allowed.');
        return;
    }

    $infra_name = self::getInfraName($infra_id);
    $date = date('Y_m_d');
    $rand = md5($original);
    $final = __DIR__ . '/../uploads/documentation_' . $area . '_' . preg_replace('/\W/','',$infra_name) . "_" . $rand . '_' . $date . '.' . $ext;

    // Save directly from the uploaded tmp file to final destination
    if (!move_uploaded_file($tmp_name, $final)) {
        $showFormWithError('Failed to save file. Please try again.');
        return;
    }

    $photo_path = basename($final);

    try {
        $stmt = $db->prepare('INSERT INTO reports (user_id, infra_id, area, description, photo_path) VALUES (?, ?, ?, ?, ?)');
        $stmt->execute([$user_id, $infra_id, $area, $description, $photo_path]);
        header('Location: /challenge/reports');
        exit;
    } catch (Exception $e) {
        if (file_exists($final)) {
            unlink($final);
        }
        $showFormWithError('Failed to save report. Please try again.');
        return;
    }
}


    public static function reports() {
        if (!isset($_SESSION['username']) || $_SESSION['username'] === 'admin') {
            header('Location: /challenge/login'); exit;
        }
        $db = Database::getInstance()->getConnection();
        $user_id = self::getUserId($_SESSION['username']);
        $stmt = $db->prepare('SELECT r.*, i.name as infra_name FROM reports r JOIN infrastructure i ON r.infra_id = i.id WHERE r.user_id = ? ORDER BY r.created_at DESC');
        $stmt->execute([$user_id]);
        $reports = $stmt->fetchAll(PDO::FETCH_ASSOC);
        require __DIR__ . '/../Views/reports.php';
    }
    private static function getUserId($username) {
        $db = Database::getInstance()->getConnection();
        $stmt = $db->prepare('SELECT id FROM users WHERE username = ?');
        $stmt->execute([$username]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);
        return $user['id'] ?? 0;
    }
    private static function getInfraName($infra_id) {
        $db = Database::getInstance()->getConnection();
        $stmt = $db->prepare('SELECT name FROM infrastructure WHERE id = ?');
        $stmt->execute([$infra_id]);
        $infra = $stmt->fetch(PDO::FETCH_ASSOC);
        return $infra['name'] ?? 'unknown';
    }

} 