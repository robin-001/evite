<?php
/**
 * Angstrom Technologies eVite Verification
 *
 * URL format:
 * https://events.angstrom-technologies.ug/evite/verify/<BASE64_TOKEN>
 *
 * Example decoded token:
 * Adeline Karemanki:+256704263862:af8238ed-8463-4e0e-972f-ae44cf038aca
 */

declare(strict_types=1);

/**
 * Get the token from the URL.
 *
 * Works with:
 * /evite/verify/<token>
 * /evite/verify.php/<token>
 */
$requestUri = $_SERVER['REQUEST_URI'] ?? '';
$path = parse_url($requestUri, PHP_URL_PATH) ?? '';

$segments = array_values(
    array_filter(explode('/', trim($path, '/')), 'strlen')
);

$token = end($segments) ?: '';

/**
 * If Apache passes the token through a query parameter as a fallback.
 */
if ($token === 'verify.php' || $token === 'verify') {
    if (!empty($_GET['token'])) {
        $token = (string) $_GET['token'];
    }
}

/**
 * Base64 URL decoding.
 *
 * Handles both normal Base64 and URL-safe Base64.
 */
function decodeBase64Token(string $token): string|false
{
    $token = strtr($token, '-_', '+/');

    // Restore Base64 padding.
    $padding = strlen($token) % 4;

    if ($padding > 0) {
        $token .= str_repeat('=', 4 - $padding);
    }

    $decoded = base64_decode($token, true);

    return $decoded === false ? false : $decoded;
}

/**
 * Escape HTML output.
 */
function e(?string $value): string
{
    return htmlspecialchars(
        $value ?? '',
        ENT_QUOTES | ENT_SUBSTITUTE,
        'UTF-8'
    );
}

$valid = false;
$name = '';
$phone = '';
$reference = '';
$error = '';

if ($token !== '') {

    $decoded = decodeBase64Token($token);

    if ($decoded !== false && $decoded !== '') {

        /*
         * Expected format:
         *
         * Name:Phone:UUID
         *
         * Split into a maximum of 3 pieces so additional colons
         * in future fields don't completely break parsing.
         */
        $parts = explode(':', $decoded);

        if (count($parts) >= 3) {

            $name = trim($parts[1]);
            $phone = trim($parts[2]);
            $reference = trim($parts[3]);

            if ($name !== '' && $phone !== '' && $reference !== '') {
                $valid = true;
            } else {
                $error = 'The verification information is incomplete.';
            }

        } else {
            $error = 'The verification code format is invalid.';
        }

    } else {
        $error = 'The verification code could not be decoded.';
    }

} else {
    $error = 'No verification code was provided.';
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <meta
        name="description"
        content="Angstrom Technologies eVite verification"
    >

    <title>
        <?= $valid ? 'Invitation Verified' : 'Verification Failed' ?>
        | Angstrom Technologies
    </title>

    <style>
        :root {
            --primary: #0b5cff;
            --primary-dark: #0647c7;
            --secondary: #00a8e8;
            --dark: #10233f;
            --text: #25364d;
            --muted: #718096;
            --background: #f4f8fc;
            --white: #ffffff;
            --success: #16a34a;
            --success-light: #ecfdf3;
            --danger: #dc2626;
            --danger-light: #fef2f2;
            --border: #e5edf6;
        }

        * {
            box-sizing: border-box;
        }

        html,
        body {
            margin: 0;
            padding: 0;
            min-height: 100%;
        }

        body {
            font-family:
                Inter,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Roboto,
                Helvetica,
                Arial,
                sans-serif;

            background:
                radial-gradient(
                    circle at 10% 10%,
                    rgba(11, 92, 255, 0.13),
                    transparent 30%
                ),
                radial-gradient(
                    circle at 90% 90%,
                    rgba(0, 168, 232, 0.12),
                    transparent 30%
                ),
                var(--background);

            color: var(--text);

            display: flex;
            flex-direction: column;

            min-height: 100vh;
        }

        /* Header */

        .header {
            width: 100%;
            padding: 24px 30px;

            display: flex;
            align-items: center;
            justify-content: center;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;

            text-decoration: none;
            color: var(--dark);
        }

        .brand-mark {
            width: 46px;
            height: 46px;

            border-radius: 12px;

            display: flex;
            align-items: center;
            justify-content: center;

            color: white;
            font-size: 20px;
            font-weight: 800;

            background:
                linear-gradient(
                    135deg,
                    var(--primary),
                    var(--secondary)
                );

            box-shadow:
                0 8px 20px rgba(11, 92, 255, 0.25);
        }

        .brand-name {
            font-size: 18px;
            font-weight: 800;
            letter-spacing: -0.3px;
        }

        .brand-tagline {
            display: block;

            margin-top: 2px;

            font-size: 10px;
            color: var(--muted);
            font-weight: 500;
        }

        /* Main */

        .main {
            flex: 1;

            display: flex;
            align-items: center;
            justify-content: center;

            padding: 30px 20px 60px;
        }

        .card {
            width: 100%;
            max-width: 520px;

            background: var(--white);

            border: 1px solid rgba(229, 237, 246, 0.9);

            border-radius: 28px;

            padding: 42px 38px;

            text-align: center;

            box-shadow:
                0 25px 70px rgba(16, 35, 63, 0.10),
                0 5px 20px rgba(16, 35, 63, 0.04);

            animation: cardIn 0.5s ease-out;
        }

        @keyframes cardIn {
            from {
                opacity: 0;
                transform: translateY(15px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Verification icon */

        .status-icon {
            width: 82px;
            height: 82px;

            margin: 0 auto 24px;

            border-radius: 50%;

            display: flex;
            align-items: center;
            justify-content: center;

            font-size: 40px;
            font-weight: 700;
        }

        .status-icon.success {
            background: var(--success-light);
            color: var(--success);

            box-shadow:
                0 0 0 10px rgba(22, 163, 74, 0.05);
        }

        .status-icon.error {
            background: var(--danger-light);
            color: var(--danger);

            box-shadow:
                0 0 0 10px rgba(220, 38, 38, 0.05);
        }

        .status-title {
            margin: 0;

            font-size: 29px;
            line-height: 1.2;

            color: var(--dark);

            letter-spacing: -0.8px;
        }

        .status-description {
            margin: 12px auto 30px;

            max-width: 390px;

            font-size: 15px;
            line-height: 1.7;

            color: var(--muted);
        }

        /* Guest information */

        .guest-card {
            margin-top: 28px;

            padding: 24px;

            border-radius: 18px;

            text-align: left;

            background:
                linear-gradient(
                    135deg,
                    #f8fbff,
                    #f1f7ff
                );

            border: 1px solid #e4edf8;
        }

        .guest-label {
            margin-bottom: 7px;

            font-size: 11px;
            font-weight: 700;

            letter-spacing: 1px;
            text-transform: uppercase;

            color: var(--muted);
        }

        .guest-name {
            margin-bottom: 20px;

            font-size: 23px;
            font-weight: 750;

            color: var(--dark);
        }

        .info-row {
            display: flex;
            align-items: center;

            gap: 13px;

            padding: 13px 0;

            border-top: 1px solid var(--border);
        }

        .info-row:first-of-type {
            border-top: none;
        }

        .info-icon {
            width: 38px;
            height: 38px;

            flex-shrink: 0;

            border-radius: 10px;

            display: flex;
            align-items: center;
            justify-content: center;

            background: white;

            color: var(--primary);

            border: 1px solid var(--border);
        }

        .info-content {
            min-width: 0;
        }

        .info-title {
            font-size: 11px;
            color: var(--muted);

            margin-bottom: 2px;
        }

        .info-value {
            font-size: 14px;
            font-weight: 650;

            color: var(--text);

            overflow-wrap: anywhere;
        }

        /* Verified badge */

        .verified-badge {
            display: inline-flex;

            align-items: center;
            gap: 7px;

            margin-top: 25px;

            padding: 8px 14px;

            border-radius: 100px;

            background: var(--success-light);

            color: var(--success);

            font-size: 12px;
            font-weight: 700;
        }

        .verified-dot {
            width: 7px;
            height: 7px;

            background: var(--success);

            border-radius: 50%;
        }

        /* Error */

        .error-box {
            margin-top: 20px;

            padding: 18px;

            border-radius: 14px;

            background: var(--danger-light);

            color: var(--danger);

            font-size: 14px;
            line-height: 1.6;
        }

        /* Footer */

        .footer {
            padding: 20px;

            text-align: center;

            font-size: 11px;

            color: var(--muted);
        }

        .footer strong {
            color: var(--dark);
        }

        /* Mobile */

        @media (max-width: 600px) {

            .header {
                padding: 20px;
            }

            .main {
                padding:
                    15px
                    15px
                    35px;
            }

            .card {
                padding:
                    35px
                    22px;

                border-radius: 22px;
            }

            .status-title {
                font-size: 25px;
            }

            .guest-card {
                padding: 20px;
            }

            .guest-name {
                font-size: 20px;
            }
        }
    </style>
</head>

<body>

<header class="header">
    <div class="brand">

        <!--
            Replace this with the official Angstrom logo if desired.

            Example:
            <img src="/assets/images/logo.png" alt="Angstrom Technologies">
        -->

        <div class="brand-mark">
            A
        </div>

        <div>
            <div class="brand-name">
                Angstrom Technologies
            </div>

            <span class="brand-tagline">
                Empowering Businesses Through Technology
            </span>
        </div>

    </div>
</header>


<main class="main">

    <section class="card">

        <?php if ($valid): ?>

            <!-- Success icon -->
            <div class="status-icon success">
                ✓
            </div>

            <h1 class="status-title">
                Invitation Verified
            </h1>

            <p class="status-description">
                This invitation has been successfully verified.
                The information below matches the verification
                code provided with the invitation.
            </p>


            <div class="guest-card">

                <div class="guest-label">
                    Invited Guest
                </div>

                <div class="guest-name">
                    <?= e($name) ?>
                </div>


                <div class="info-row">

                    <div class="info-icon">
                        <!-- Phone icon -->
                        <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                        >
                            <path d="M22 16.92v3a2 2 0 0 1-2.18 2
                                     19.79 19.79 0 0 1-8.63-3.07
                                     19.5 19.5 0 0 1-6-6
                                     19.79 19.79 0 0 1-3.07-8.67
                                     A2 2 0 0 1 4.11 2h3
                                     a2 2 0 0 1 2 1.72
                                     12.84 12.84 0 0 0 .7 2.81
                                     2 2 0 0 1-.45 2.11L8.09 9.91
                                     a16 16 0 0 0 6 6l1.27-1.27
                                     a2 2 0 0 1 2.11-.45
                                     12.84 12.84 0 0 0 2.81.7
                                     A2 2 0 0 1 22 16.92z"
                            />
                        </svg>
                    </div>

                    <div class="info-content">

                        <div class="info-title">
                            Phone Number
                        </div>

                        <div class="info-value">
                            <?= e($phone) ?>
                        </div>

                    </div>

                </div>


                <div class="info-row">

                    <div class="info-icon">
                        <!-- Shield/check icon -->
                        <svg
                            width="18"
                            height="18"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                        >
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7
                                     c0 6 8 10 8 10z"
                            />

                            <path d="m9 12 2 2 4-4"/>
                        </svg>
                    </div>

                    <div class="info-content">

                        <div class="info-title">
                            Verification Reference
                        </div>

                        <div class="info-value">
                            <?= e($reference) ?>
                        </div>

                    </div>

                </div>

            </div>


            <div class="verified-badge">

                <span class="verified-dot"></span>

                Verified Invitation

            </div>

        <?php else: ?>

            <!-- Error icon -->
            <div class="status-icon error">
                !
            </div>

            <h1 class="status-title">
                Verification Failed
            </h1>

            <p class="status-description">
                We could not verify this invitation code.
                Please make sure you are using the complete
                invitation verification link.
            </p>

            <div class="error-box">
                <?= e($error) ?>
            </div>

        <?php endif; ?>

    </section>

</main>


<footer class="footer">

    <strong>Angstrom Technologies Limited</strong>
    <br>

    Empowering Businesses Through Technology

</footer>

</body>
</html>