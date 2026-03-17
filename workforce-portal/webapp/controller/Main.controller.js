sap.ui.define(
  ["sap/ui/core/mvc/Controller", "sap/m/MessageBox", "sap/m/MessageToast"],
  function (Controller, MessageBox, MessageToast) {
    "use strict";

    return Controller.extend("my.app.controller.Main", {
      onAfterRendering: function () {
        this.onRefreshButtonPress();
      },

      onRefreshButtonPress: async function () {
        const oView = this.getView();
        const token = localStorage.getItem("authToken");

        if (!token) {
          this.getOwnerComponent().getRouter().navTo("Login");
          return;
        }

        try {
          const res = await fetch("/api/auth/me", {
            method: "GET",
            headers: {
              Authorization: "Bearer " + token,
            },
          });

          const data = await res.json().catch(function () {
            return null;
          });

          if (!res.ok || !data || !data.username) {
            localStorage.removeItem("authToken");
            MessageBox.error(
              (data && (data.detail || data.message)) || "Not authenticated",
            );
            this.getOwnerComponent().getRouter().navTo("Login");
            return;
          }

          oView
            .byId("idLoggedInAsLoadingUserText")
            .setText("Logged in as: " + data.username);
        } catch (e) {
          MessageBox.error("Service is not reachable. Please try again.");
        }
      },

      onMyProfilePress: function () {
        this.getOwnerComponent().getRouter().navTo("MyProfile");
      },

      onLogoutButtonPress: function () {
        localStorage.removeItem("authToken");
        MessageToast.show("Signed out");
        this.getOwnerComponent().getRouter().navTo("Login");
      },
    });
  },
);
