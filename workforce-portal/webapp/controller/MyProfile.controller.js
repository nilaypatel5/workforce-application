sap.ui.define(
  [
    "sap/ui/core/mvc/Controller",
    "sap/m/MessageBox",
    "sap/ui/model/json/JSONModel",
  ],
  function (Controller, MessageBox, JSONModel) {
    "use strict";

    return Controller.extend("my.app.controller.MyProfile", {
      onInit: function () {
        this._loadProfile();
      },

      _loadProfile: async function () {
        const token = localStorage.getItem("authToken");
        if (!token) {
          console.warn("No auth token found, redirecting to login");
          this.getOwnerComponent().getRouter().navTo("Login");
          return;
        }

        try {
          const res = await fetch("/api/ess/profile", {
            method: "GET",
            headers: {
              Authorization: "Bearer " + token,
              "Content-Type": "application/json",
            },
          });

          console.log("[Profile] Response status:", res.status);

          const data = await res.json().catch(() => null);

          if (!res.ok || !data) {
            let sMessage;
            switch (res.status) {
              case 401:
                sMessage =
                  (data && (data.detail || data.message)) ||
                  "Not authenticated. Please sign in again.";
                localStorage.removeItem("authToken");
                this.getOwnerComponent().getRouter().navTo("Login");
                break;
              case 404:
                sMessage =
                  (data && (data.detail || data.message)) ||
                  "Employee profile not found for this user.";
                break;
              case 500:
                sMessage =
                  (data && (data.detail || data.message)) ||
                  "Server error while loading profile.";
                break;
              case 503:
                sMessage =
                  (data && (data.detail || data.message)) ||
                  "Backend service or database is currently unavailable.";
                break;
              default:
                sMessage =
                  (data && (data.detail || data.message)) ||
                  "Could not load profile. (HTTP " + res.status + ")";
            }

            console.error("[Profile] Error:", sMessage);
            MessageBox.error(sMessage);
            return;
          }

          console.log("[Profile] Data loaded:", data);

          const oModel = new JSONModel(data);
          this.getView().setModel(oModel, "profileModel");
        } catch (e) {
          console.error("[Profile] Fetch error:", e);
          MessageBox.error(
            "Cannot reach backend service. Please check if the Flask server is running.",
          );
        }
      },
    });
  },
);
