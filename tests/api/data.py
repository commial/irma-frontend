test_routes = {
    "/probes": ["GET"],
    "/search/files": ["GET"],
    "/files/<filesha256>": ["GET"],
    "/scans": ["GET", "POST"],
    "/scans/<scanid>": ["GET"],
    "/scans/<scanid>/files": ["POST"],
    "/scans/<scanid>/launch": ["POST"],
    "/scans/<scanid>/cancel": ["POST"],
    "/scans/<scanid>/results": ["GET"],
    "/scans/<scanid>/results/<resultid:int>": ["GET"]
}
