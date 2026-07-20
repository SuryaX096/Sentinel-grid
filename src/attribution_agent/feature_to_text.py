def translate_features_to_description(features: list, anomaly_score: float = 0.5) -> str:
    """
    Translates a list of flagged network flow features into a natural-language
    security description of the observed behavior.
    """
    if not features:
        return "Anomalous connection flow patterns detected with low similarity to normal baseline profiles."
        
    translations = []
    
    # Mapping of features to security explanations
    feature_mappings = {
        "serror_rate": "an elevated rate of connection attempts resulting in SYN errors, indicating potential SYN flooding or port scanning",
        "srv_serror_rate": "SYN errors occurring across multiple instances of the same service, hinting at a coordinated denial of service sweep",
        "rerror_rate": "a high percentage of connections rejected with RST flags, typical of port scans probing closed ports",
        "srv_rerror_rate": "widespread connection rejections on active services, suggesting port scanning or active denial of service attempts",
        "wrong_fragment": "presence of malformed or fragmented IP packets, which is a signature of denial-of-service exploits (like teardrop) or firewall evasion techniques",
        "land": "a spoofed land attack where the source IP address and port match the destination IP address and port",
        "duration": "connections remaining open for an unusually long duration, potentially indicating unauthorized interactive shells, data exfiltration, or slow-rate denial of service",
        "src_bytes": "anomalously high volume of outbound data transmitted from the source host, suggesting data exfiltration or massive payload injection",
        "dst_bytes": "anomalously high volume of inbound data received by the host, typical of large payloads, exploit attempts, or file downloads",
        "src_bytes/dst_bytes ratio": "unusual ratio of outbound to inbound data volume, showing asymmetric traffic patterns typical of file exfiltration or shell connection tunnels",
        "num_failed_logins": "multiple consecutive failed login attempts on authentication services, representing active brute-force password guessing",
        "logged_in": "anomalous access patterns despite successful login, suggesting potential account compromise or unauthorized post-auth activity",
        "hot": "frequent access to sensitive administrative commands, directories, or indicators (e.g., hot features or system files)",
        "num_compromised": "indicators of system compromise or state alteration detected during connection",
        "root_shell": "an interactive root or administrative shell spawned, indicating severe user privilege escalation",
        "su_attempted": "attempts to escalate user privileges to root using commands like su",
        "num_access_files": "unusual access to local files during a session, typical of local directory traversal or sensitive file enumeration",
        "num_shells": "multiple command shells spawned during a single remote connection",
        "count": "a rapid spike in the volume of connection attempts to the same host in a short time window (typical of volumetric flooding)",
        "srv_count": "a high density of connections targeting the same service within a narrow time window, typical of service-specific flooding",
        "connection frequency ratio": "anomalous ratio of connections to the same host vs. the same service, signaling targeted service scanning",
        "diff_srv_rate": "a high rate of connections to different services on the destination host, indicating active port scanning",
        "dst_host_diff_srv_rate": "probing a wide range of services on the destination endpoint, showing active network service discovery",
        "dst_host_same_src_port_rate": "rapid connection attempts originating from a single source port, indicative of port sweeps",
        "dst_host_srv_diff_host_rate": "connections for the same service distributed across multiple distinct destination hosts, indicating active network sweeps",
        "dst_host_srv_count": "unusual density of service connections on the destination host over a rolling window",
        "dst_host_serror_rate": "sustained SYN errors observed at the destination host, confirming target-side denial of service effects",
        "dst_host_srv_serror_rate": "systemic service-level SYN errors on the destination host, indicating target service starvation",
        "dst_host_rerror_rate": "sustained RST connection rejections recorded on the destination host",
        "dst_host_srv_rerror_rate": "sustained service-level connection rejections recorded on the destination host"
    }
    
    for feature in features:
        # Check direct match or lowercase match
        trans = feature_mappings.get(feature) or feature_mappings.get(feature.lower())
        if trans:
            translations.append(trans)
            
    if not translations:
        # Generic backup translation using the feature names
        joined_feats = ", ".join(features)
        return f"Anomalous flow behavior characterized by deviations in the following parameters: {joined_feats}. Anomaly score: {anomaly_score:.2f}."
        
    # Build grammatically clean description
    if len(translations) == 1:
        desc = f"The anomaly exhibits {translations[0]}."
    elif len(translations) == 2:
        desc = f"The anomaly exhibits {translations[0]}, along with {translations[1]}."
    else:
        desc = f"The anomaly exhibits {', '.join(translations[:-1])}, and is accompanied by {translations[-1]}."
        
    desc += f" Overall anomaly threat confidence: {anomaly_score:.2%}."
    return desc

if __name__ == "__main__":
    test_feats = ["num_failed_logins", "duration"]
    print(translate_features_to_description(test_feats, 0.89))
