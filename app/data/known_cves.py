KNOWN_CVES = [
    # --- Cluster: RCE in web frameworks / enterprise software ---
    {"cve_id": "CVE-2021-44228", "question": "What vulnerability let attackers run arbitrary code remotely through a widely-used Java logging library, discovered in December 2021?"},
    {"cve_id": "CVE-2021-45046", "question": "What follow-up flaw in the same Java logging library remained exploitable in certain non-default configurations after the initial patch?"},
    {"cve_id": "CVE-2017-5638", "question": "What flaw in Apache Struts' file upload parser allowed remote code execution and led to a major credit bureau breach?"},
    {"cve_id": "CVE-2018-11776", "question": "What Apache Struts vulnerability allowed remote code execution via crafted namespace values in the URL?"},
    {"cve_id": "CVE-2018-7600", "question": "What Drupal vulnerability, nicknamed after a well-known movie reference, allowed remote code execution on unpatched sites?"},
    {"cve_id": "CVE-2022-22965", "question": "What Spring Framework vulnerability, discovered in 2022, allowed remote code execution via data binding on JDK 9 and above?"},
    {"cve_id": "CVE-2022-22963", "question": "What Spring Cloud Function vulnerability allowed remote code execution through a crafted SpEL expression in a routing header?"},
    {"cve_id": "CVE-2022-26134", "question": "What Atlassian Confluence vulnerability allowed unauthenticated remote code execution via OGNL injection?"},
    {"cve_id": "CVE-2021-26084", "question": "What earlier Atlassian Confluence vulnerability allowed OGNL injection leading to remote code execution?"},
    {"cve_id": "CVE-2023-22515", "question": "What Confluence Data Center vulnerability allowed attackers to create unauthorized administrator accounts?"},
    {"cve_id": "CVE-2021-22205", "question": "What GitLab vulnerability allowed remote code execution via image file processing during upload?"},
    {"cve_id": "CVE-2023-49070", "question": "What Apache OFBiz vulnerability allowed unauthenticated remote code execution via an XML-RPC endpoint?"},

    # --- Cluster: Privilege escalation ---
    {"cve_id": "CVE-2016-5195", "question": "What Linux kernel race condition allowed local privilege escalation via copy-on-write memory handling?"},
    {"cve_id": "CVE-2022-0847", "question": "What Linux kernel vulnerability, nicknamed after a plumbing-related pun, allowed overwriting read-only files via a pipe flaw?"},
    {"cve_id": "CVE-2021-4034", "question": "What Linux polkit vulnerability allowed any unprivileged local user to gain root access?"},
    {"cve_id": "CVE-2021-3156", "question": "What heap overflow bug in sudo allowed local privilege escalation to root?"},
    {"cve_id": "CVE-2021-34527", "question": "What Windows Print Spooler vulnerability allowed remote code execution with system privileges?"},

    # --- Cluster: Auth bypass / SSRF / spoofing ---
    {"cve_id": "CVE-2021-26855", "question": "What server-side request forgery flaw in Microsoft Exchange allowed attackers to bypass authentication?"},
    {"cve_id": "CVE-2020-1472", "question": "What flaw in the Netlogon protocol allowed an attacker to impersonate a domain controller?"},
    {"cve_id": "CVE-2020-0601", "question": "What Windows CryptoAPI vulnerability allowed spoofing of digital certificate validation?"},
    {"cve_id": "CVE-2021-21972", "question": "What VMware vCenter Server vulnerability allowed unauthenticated remote code execution via a plugin?"},
    {"cve_id": "CVE-2022-40684", "question": "What Fortinet FortiOS vulnerability allowed authentication bypass on the administrative interface?"},
    {"cve_id": "CVE-2023-4966", "question": "What Citrix NetScaler vulnerability, nicknamed after a blood-related term, allowed session token theft?"},
    {"cve_id": "CVE-2024-21887", "question": "What Ivanti Connect Secure vulnerability allowed authenticated command injection?"},
    {"cve_id": "CVE-2023-46805", "question": "What earlier Ivanti Connect Secure vulnerability allowed authentication bypass on the web component?"},

    # --- Cluster: Remote network service exploitation ---
    {"cve_id": "CVE-2017-0144", "question": "What Windows SMB vulnerability was exploited by the WannaCry ransomware worm?"},
    {"cve_id": "CVE-2019-0708", "question": "What Remote Desktop Services vulnerability could be exploited without authentication, similar to WannaCry's spread pattern?"},
    {"cve_id": "CVE-2014-0160", "question": "Which bug in OpenSSL's heartbeat extension leaked memory contents including private keys?"},
    {"cve_id": "CVE-2014-6271", "question": "What bash shell bug allowed attackers to execute commands via crafted environment variables?"},
    {"cve_id": "CVE-2019-19781", "question": "What Citrix Application Delivery Controller flaw allowed directory traversal and remote code execution?"},
    {"cve_id": "CVE-2023-34362", "question": "What MOVEit Transfer vulnerability allowed unauthenticated SQL injection leading to data theft at scale?"},

    # --- Cluster: Office / client-side document exploitation ---
    {"cve_id": "CVE-2017-0199", "question": "What Microsoft Office vulnerability allowed code execution via a malicious OLE2 document?"},
    {"cve_id": "CVE-2022-30190", "question": "What Microsoft Windows Support Diagnostic Tool vulnerability, nicknamed after a plant, allowed code execution via crafted Office documents?"},

    # --- Cluster: Misc / supply chain / other ---
    {"cve_id": "CVE-2024-3094", "question": "What backdoor was discovered in the XZ Utils compression library, inserted through a multi-year supply chain compromise?"},
    {"cve_id": "CVE-2024-27198", "question": "What JetBrains TeamCity vulnerability allowed authentication bypass on the web server component?"},
    {"cve_id": "CVE-2024-1709", "question": "What ConnectWise ScreenConnect vulnerability allowed authentication bypass via an alternate path?"},
    {"cve_id": "CVE-2023-27350", "question": "What PaperCut print management software vulnerability allowed unauthenticated remote code execution?"},
    {"cve_id": "CVE-2022-42889", "question": "What Apache Commons Text vulnerability, nicknamed after a spell-like reference to the Log4Shell bug, allowed remote code execution via string interpolation?"},

    # --- Additional entries to round out the set ---
    {"cve_id": "CVE-2021-44832", "question": "What additional Log4j vulnerability allowed remote code execution when an attacker controlled the logging configuration?"},
    {"cve_id": "CVE-2022-1388", "question": "What F5 BIG-IP vulnerability allowed unauthenticated attackers to execute arbitrary system commands?"},
    {"cve_id": "CVE-2023-3519", "question": "What Citrix NetScaler ADC vulnerability allowed unauthenticated remote code execution?"},
    {"cve_id": "CVE-2020-3452", "question": "What Cisco ASA and FTD vulnerability allowed unauthenticated directory traversal to read sensitive files?"},
    {"cve_id": "CVE-2021-22986", "question": "What F5 BIG-IP iControl REST vulnerability allowed unauthenticated remote code execution?"},
    {"cve_id": "CVE-2020-5902", "question": "What F5 BIG-IP TMUI vulnerability allowed unauthenticated remote code execution via the management interface?"},
    {"cve_id": "CVE-2019-11510", "question": "What Pulse Secure VPN vulnerability allowed unauthenticated attackers to read arbitrary files including credentials?"},
    {"cve_id": "CVE-2018-13379", "question": "What Fortinet SSL VPN vulnerability allowed unauthenticated attackers to read system files via path traversal?"},
    {"cve_id": "CVE-2021-40444", "question": "What Microsoft Windows MSHTML vulnerability allowed remote code execution via malicious Office documents?"},
    {"cve_id": "CVE-2022-41040", "question": "What Microsoft Exchange vulnerability, part of a pair nicknamed after a well-known duo, allowed server-side request forgery?"},
    {"cve_id": "CVE-2022-41082", "question": "What paired Microsoft Exchange vulnerability allowed remote code execution when combined with the related SSRF flaw?"},
    {"cve_id": "CVE-2023-23397", "question": "What Microsoft Outlook vulnerability allowed credential theft via a specially crafted email with no user interaction required?"},
]