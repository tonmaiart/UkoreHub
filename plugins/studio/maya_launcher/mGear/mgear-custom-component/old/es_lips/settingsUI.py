# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settingsUI.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(305, 351)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.checkBox_enable_zipper = QCheckBox(Form)
        self.checkBox_enable_zipper.setObjectName(u"checkBox_enable_zipper")
        self.checkBox_enable_zipper.setEnabled(False)

        self.gridLayout.addWidget(self.checkBox_enable_zipper, 1, 0, 1, 1)

        self.checkBox_auto_pinch = QCheckBox(Form)
        self.checkBox_auto_pinch.setObjectName(u"checkBox_auto_pinch")

        self.gridLayout.addWidget(self.checkBox_auto_pinch, 3, 0, 1, 1)

        self.widget = QWidget(Form)
        self.widget.setObjectName(u"widget")
        self.gridLayout_2 = QGridLayout(self.widget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.checkBox_ignore_extra_joints = QCheckBox(self.widget)
        self.checkBox_ignore_extra_joints.setObjectName(u"checkBox_ignore_extra_joints")

        self.gridLayout_2.addWidget(self.checkBox_ignore_extra_joints, 0, 0, 1, 1)

        self.plainTextEdit = QPlainTextEdit(self.widget)
        self.plainTextEdit.setObjectName(u"plainTextEdit")
        self.plainTextEdit.setMaximumSize(QSize(16777215, 30))
        self.plainTextEdit.setReadOnly(True)

        self.gridLayout_2.addWidget(self.plainTextEdit, 1, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 359, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 2, 0, 1, 1)


        self.gridLayout.addWidget(self.widget, 4, 0, 1, 2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.checkBox_enable_sliding = QCheckBox(Form)
        self.checkBox_enable_sliding.setObjectName(u"checkBox_enable_sliding")

        self.horizontalLayout.addWidget(self.checkBox_enable_sliding)

        self.lineEdit_sliding_object = QLineEdit(Form)
        self.lineEdit_sliding_object.setObjectName(u"lineEdit_sliding_object")

        self.horizontalLayout.addWidget(self.lineEdit_sliding_object)


        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 2)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.checkBox_enable_zipper.setText(QCoreApplication.translate("Form", u"Enable Zipper", None))
        self.checkBox_auto_pinch.setText(QCoreApplication.translate("Form", u"Auto Pinch", None))
        self.checkBox_ignore_extra_joints.setText(QCoreApplication.translate("Form", u"Ignore Extra Joints", None))
        self.plainTextEdit.setPlainText(QCoreApplication.translate("Form", u"This will Ignore Guide 02 and 03", None))
        self.checkBox_enable_sliding.setText(QCoreApplication.translate("Form", u"Enable Sliding", None))
    # retranslateUi

