sap.ui.define(
  ["sap/ui/core/mvc/Controller", "sap/m/MessageBox", "sap/m/MessageToast"],
  function (Controller, MessageBox, MessageToast) {
    "use strict";

    return Controller.extend("my.app.controller.Login", {
      onInputLoginSubmit: function () {
        return this.onSignInButtonPress();
      },

      onSignInButtonPress: async function () {
        const oView = this.getView();
        const username = (
          oView.byId("idUsernameInput").getValue() || ""
        ).trim();
        const password = oView.byId("idPasswordInput").getValue();

        if (!username || !password) {
          MessageBox.warning("Please enter your username and password.");
          return;
        }

        try {
          const res = await fetch("/api/auth/login", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ username: username, password: password }),
          });

          const data = await res.json().catch(() => null);

          if (!res.ok || !data || !data.success) {
            MessageBox.error(
              (data && data.message) || "Sign-in failed. Please try again.",
            );
            return;
          }

          localStorage.setItem("authToken", data.token);
          MessageToast.show(data.message || "Signed in");
          this.getOwnerComponent().getRouter().navTo("Main");
        } catch (e) {
          MessageBox.error(
            "Service is not reachable. Please check the backend and try again.",
          );
        }
      },
    });
  },
);
