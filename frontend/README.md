# React Dashboard (Staff View)

Recommended widgets for the staff dashboard:

- Current occupancy
- Entry / Exit counter
- Heatmap image overlay
- Live alert notifications
- Peak hour chart

Expected API/WebSocket contracts:

- `GET /health`
- `POST /alerts/occupancy`
- `POST /alerts/loitering`
- `WS /ws/occupancy`
