sap.ui.define(
  [
    "sap/ui/core/mvc/Controller",
    "sap/m/MessageBox",
    "sap/m/MessageToast",
    "sap/ui/model/json/JSONModel",
    "sap/m/Dialog",
    "sap/m/Label",
    "sap/m/TextArea",
    "sap/m/Button",
    "sap/ui/layout/form/SimpleForm",
  ],
  function (
    Controller,
    MessageBox,
    MessageToast,
    JSONModel,
    Dialog,
    Label,
    TextArea,
    Button,
    SimpleForm,
  ) {
    "use strict";

    return Controller.extend("my.app.controller.TeamLeaveApprovals", {
      onInit: function () {
        const oModel = new JSONModel({ items: [] });
        this.getView().setModel(oModel, "pendingModel");
        this.loadPending();
      },

      ensureAuthenticated: function () {
        const token = localStorage.getItem("authToken");
        if (!token) {
          this.getOwnerComponent().getRouter().navTo("Login");
          return null;
        }
        return token;
      },

      loadPending: async function () {
        const token = this.ensureAuthenticated();
        if (!token) {
          return;
        }

        try {
          const res = await fetch("/api/manager/leaves/pending", {
            method: "GET",
            headers: {
              Authorization: "Bearer " + token,
              "Content-Type": "application/json",
            },
          });

          const data = await res.json().catch(function () {
            return null;
          });

          if (res.status === 403) {
            MessageBox.error(
              (data && (data.detail || data.message)) ||
                "You do not have manager access.",
            );
            this.getOwnerComponent().getRouter().navTo("Main");
            return;
          }

          if (!res.ok || !Array.isArray(data)) {
            const sMessage =
              (data && (data.detail || data.message)) ||
              "Could not load pending leave requests.";
            MessageBox.error(sMessage);
            return;
          }

          this.getView().getModel("pendingModel").setProperty("/items", data);
        } catch (e) {
          MessageBox.error(
            "Cannot reach backend service. Please check if the Flask server is running.",
          );
        }
      },

      onRefreshButtonPress: function () {
        this.loadPending();
      },

      _getPendingRowContext: function (oEvent) {
        const oBtn = oEvent.getSource();
        let oCtx = oBtn.getBindingContext("pendingModel");
        if (!oCtx) {
          const p = oBtn.getParent();
          if (p && p.getBindingContext) {
            oCtx = p.getBindingContext("pendingModel");
          }
          if (!oCtx && p && p.getParent && p.getParent().getBindingContext) {
            oCtx = p.getParent().getBindingContext("pendingModel");
          }
        }
        return oCtx;
      },

      onApproveButtonPress: function (oEvent) {
        const oCtx = this._getPendingRowContext(oEvent);
        const oRow = oCtx && oCtx.getObject();
        if (!oRow || !oRow.id) {
          MessageBox.error("Could not read leave request.");
          return;
        }
        this._openCommentDialog(
          "Approve leave",
          "Optional comment for the employee",
          "Approve",
          this._callApprove.bind(this, oRow.id),
        );
      },

      onRejectButtonPress: function (oEvent) {
        const oCtx = this._getPendingRowContext(oEvent);
        const oRow = oCtx && oCtx.getObject();
        if (!oRow || !oRow.id) {
          MessageBox.error("Could not read leave request.");
          return;
        }
        this._openCommentDialog(
          "Reject leave",
          "Optional reason (shown to the employee)",
          "Reject",
          this._callReject.bind(this, oRow.id),
        );
      },

      _openCommentDialog: function (sTitle, sPlaceholder, sConfirm, fnAction) {
        const that = this;

        if (this.oCommentDialog) {
          this.oCommentDialog.destroy();
          this.oCommentDialog = null;
        }

        const oComment = new TextArea({
          width: "100%",
          rows: 3,
          placeholder: sPlaceholder,
        });

        const oForm = new SimpleForm({
          editable: true,
          layout: "ResponsiveGridLayout",
          content: [new Label({ text: "Comment" }), oComment],
        });

        this.oCommentDialog = new Dialog({
          title: sTitle,
          contentWidth: "28rem",
          content: [oForm],
          beginButton: new Button({
            text: sConfirm,
            type: "Emphasized",
            press: function () {
              const s = oComment.getValue().trim();
              fnAction(s.length ? s : null);
              that.oCommentDialog.close();
            },
          }),
          endButton: new Button({
            text: "Cancel",
            press: function () {
              that.oCommentDialog.close();
            },
          }),
          afterClose: function () {
            if (that.oCommentDialog) {
              that.oCommentDialog.destroy();
              that.oCommentDialog = null;
            }
          },
        });

        this.getView().addDependent(this.oCommentDialog);
        this.oCommentDialog.open();
      },

      _callApprove: async function (nId, sComment) {
        const token = this.ensureAuthenticated();
        if (!token) {
          return;
        }

        try {
          const res = await fetch("/api/manager/leaves/" + nId + "/approve", {
            method: "PUT",
            headers: {
              Authorization: "Bearer " + token,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ comment: sComment }),
          });

          const data = await res.json().catch(function () {
            return null;
          });

          if (!res.ok) {
            MessageBox.error(
              (data && (data.detail || data.message)) ||
                "Could not approve leave request.",
            );
            return;
          }

          MessageToast.show("Leave approved.");
          this.loadPending();
        } catch (e) {
          MessageBox.error(
            "Cannot reach backend service. Please check if the Flask server is running.",
          );
        }
      },

      _callReject: async function (nId, sComment) {
        const token = this.ensureAuthenticated();
        if (!token) {
          return;
        }

        try {
          const res = await fetch("/api/manager/leaves/" + nId + "/reject", {
            method: "PUT",
            headers: {
              Authorization: "Bearer " + token,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ comment: sComment }),
          });

          const data = await res.json().catch(function () {
            return null;
          });

          if (!res.ok) {
            MessageBox.error(
              (data && (data.detail || data.message)) ||
                "Could not reject leave request.",
            );
            return;
          }

          MessageToast.show("Leave rejected.");
          this.loadPending();
        } catch (e) {
          MessageBox.error(
            "Cannot reach backend service. Please check if the Flask server is running.",
          );
        }
      },
    });
  },
);
