<?php
/**
 * Redirect /evite/download/ to the verification page.
 *
 * Prevents the Apache directory index from listing the e-vite PDFs.
 * Requests for actual .pdf files inside this directory are unaffected.
 */
header(
    'Location: https://events.angstrom-technologies.ug/evite/verify.php',
    true,
    302
);
exit;
